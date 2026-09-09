use clap::{Parser, ValueEnum};
use kg_sim::{Config, MarketOverlay, Outcome, PreparedTape, Replay, Tape};
use rayon::prelude::*;
use serde_json::Value;
use std::{
    collections::HashMap,
    fs::File,
    io::{self, BufReader, BufWriter, Write},
    path::{Path, PathBuf},
    process::ExitCode,
    sync::Arc,
};

type Result<T> = std::result::Result<T, String>;

#[derive(Clone, Copy, Debug, ValueEnum)]
enum StepMode {
    /// Match Kaggle episodeSteps: 720 recorded states = 719 action turns.
    Kaggle,
    /// Execute exactly --steps action turns (including the last daily refresh).
    Turns,
}

#[derive(Parser, Debug)]
#[command(
    version,
    about = "Deterministic Kaggriculture 1.32.7 tape simulator (shared market, Rayon batches)"
)]
struct Args {
    #[arg(long, required_unless_present = "jobs", conflicts_with = "jobs")]
    tape_a: Option<PathBuf>,
    #[arg(long, required_unless_present = "jobs", conflicts_with = "jobs")]
    tape_b: Option<PathBuf>,
    /// Optional state-dependent market profiles in input A/B order.
    #[arg(long, conflicts_with = "jobs")]
    overlay_a: Option<PathBuf>,
    #[arg(long, conflicts_with = "jobs")]
    overlay_b: Option<PathBuf>,
    #[arg(
        long,
        required_unless_present = "jobs",
        conflicts_with = "jobs",
        allow_hyphen_values = true
    )]
    seed: Option<i64>,
    /// CSV: seed,tape_a,tape_b,reverse. Paths are relative to the CSV's directory.
    #[arg(long)]
    jobs: Option<PathBuf>,
    /// Horizon; defaults to episodeSteps in --config, otherwise 720.
    #[arg(long)]
    steps: Option<usize>,
    #[arg(long, value_enum, default_value_t = StepMode::Kaggle)]
    step_mode: StepMode,
    #[arg(long, conflicts_with = "jobs")]
    reverse_seats: bool,
    /// Reproduce the example agent's hand-list slicing BEFORE atomic PLANT validation.
    #[arg(long)]
    trim_hands: bool,
    /// Trim only input tape A's hands (useful for a candidate vs a raw recorded opponent).
    #[arg(long)]
    trim_hands_a: bool,
    /// Trim only input tape B's hands. These flags follow tapes when seats are reversed.
    #[arg(long)]
    trim_hands_b: bool,
    /// Flat configuration overrides or a full Kaggle specification JSON.
    #[arg(long)]
    config: Option<PathBuf>,
    /// Rayon worker count; if omitted, respects RAYON_NUM_THREADS.
    #[arg(long, requires = "jobs")]
    threads: Option<usize>,
    /// Write initial state + every post-turn mechanics state as JSONL (slow diagnostics).
    #[arg(long, conflicts_with = "jobs")]
    trace: Option<PathBuf>,
}

fn read_json(path: &Path) -> Result<Value> {
    let file = File::open(path).map_err(|e| format!("{}: {e}", path.display()))?;
    serde_json::from_reader(BufReader::new(file)).map_err(|e| format!("{}: {e}", path.display()))
}

struct TapeCache<'a> {
    config: &'a Config,
    turns: usize,
    entries: HashMap<PathBuf, Result<Arc<PreparedTape>>>,
}

impl TapeCache<'_> {
    fn load(&mut self, path: &Path) -> Result<Arc<PreparedTape>> {
        // The Python batch client supplies canonical paths. Avoid a filesystem
        // round trip for every repeated seed while keeping relative paths valid.
        if let Some(cached) = self.entries.get(path) {
            return cached.clone();
        }
        let path = path
            .canonicalize()
            .map_err(|e| format!("{}: {e}", path.display()))?;
        self.entries
            .entry(path.clone())
            .or_insert_with(|| {
                let tape = Tape::from_json(&read_json(&path)?)
                    .map_err(|e| format!("{}: {e}", path.display()))?;
                Ok(Arc::new(PreparedTape::new(tape, self.config, self.turns)))
            })
            .clone()
    }
}

#[derive(Default)]
struct OverlayCache {
    entries: HashMap<PathBuf, Result<Arc<MarketOverlay>>>,
}

impl OverlayCache {
    fn load_optional(&mut self, path: &Path) -> Result<Option<Arc<MarketOverlay>>> {
        if path.as_os_str().is_empty() {
            return Ok(None);
        }
        let path = path
            .canonicalize()
            .map_err(|e| format!("{}: {e}", path.display()))?;
        self.entries
            .entry(path.clone())
            .or_insert_with(|| {
                let profile = MarketOverlay::from_json(&read_json(&path)?)
                    .map_err(|e| format!("{}: {e}", path.display()))?;
                Ok(Arc::new(profile))
            })
            .clone()
            .map(Some)
    }
}

struct Job {
    seed: i64,
    a: Arc<PreparedTape>,
    b: Arc<PreparedTape>,
    overlays: [Option<Arc<MarketOverlay>>; 2],
    reverse: bool,
}

fn parse_job(
    record: &csv::StringRecord,
    dir: &Path,
    cache: &mut TapeCache<'_>,
    overlays: &mut OverlayCache,
) -> Result<Job> {
    if record.len() != 4 && record.len() != 6 {
        return Err("expected CSV fields seed,tape_a,tape_b,reverse[,overlay_a,overlay_b]".into());
    }
    let seed = record[0]
        .parse::<i64>()
        .map_err(|e| format!("invalid seed: {e}"))?;
    let reverse = match record[3].to_ascii_lowercase().as_str() {
        "0" | "false" => false,
        "1" | "true" => true,
        _ => return Err("reverse must be 0, 1, false, or true".into()),
    };
    if record[1].is_empty() || record[2].is_empty() {
        return Err("tape paths must not be empty".into());
    }
    let a = cache.load(&dir.join(&record[1]))?;
    let b = cache.load(&dir.join(&record[2]))?;
    let profiles = if record.len() == 6 {
        [
            overlays.load_optional(&dir.join(&record[4]))?,
            overlays.load_optional(&dir.join(&record[5]))?,
        ]
    } else {
        [None, None]
    };
    Ok(Job {
        seed,
        a,
        b,
        overlays: profiles,
        reverse,
    })
}

fn write_json_line(writer: &mut impl Write, value: &impl serde::Serialize) -> Result<()> {
    serde_json::to_writer(&mut *writer, value).map_err(|e| e.to_string())?;
    writer.write_all(b"\n").map_err(|e| e.to_string())
}

fn execute(args: Args) -> Result<bool> {
    let config = match &args.config {
        Some(path) => Config::from_json(&read_json(path)?)?,
        None => Config::default(),
    };
    let steps = args.steps.unwrap_or(config.episode_steps);
    if steps > i32::MAX as usize {
        return Err("--steps exceeds i32::MAX".into());
    }
    let turns =
        match args.step_mode {
            StepMode::Kaggle if steps == 0 => return Err(
                "Kaggle episodeSteps must be >= 1; use --step-mode turns for a zero-turn replay"
                    .into(),
            ),
            // Kaggle's reset starts ACTIVE even for episodeSteps=1: one action still runs.
            StepMode::Kaggle => steps.saturating_sub(1).max(1),
            StepMode::Turns => steps,
        };
    if args.threads == Some(0) {
        return Err("--threads must be >= 1".into());
    }
    let trim_hands = [
        args.trim_hands || args.trim_hands_a,
        args.trim_hands || args.trim_hands_b,
    ];
    let mut cache = TapeCache {
        config: &config,
        turns,
        entries: HashMap::new(),
    };
    let mut overlay_cache = OverlayCache::default();
    let mut stdout = BufWriter::new(io::stdout().lock());
    let failed;
    if let Some(path) = &args.jobs {
        let file = File::open(path).map_err(|e| format!("{}: {e}", path.display()))?;
        let dir = path.parent().unwrap_or_else(|| Path::new("."));
        let mut reader = csv::ReaderBuilder::new()
            .has_headers(false)
            .flexible(true)
            .trim(csv::Trim::All)
            .from_reader(file);
        let mut jobs = Vec::new();
        for (i, record) in reader.records().enumerate() {
            let parsed = record.map_err(|e| e.to_string()).and_then(|r| {
                let is_header = i == 0
                    && r.get(0) == Some("seed")
                    && r.get(1) == Some("tape_a")
                    && r.get(2) == Some("tape_b")
                    && r.get(3) == Some("reverse");
                if is_header {
                    return Ok(None);
                }
                parse_job(&r, dir, &mut cache, &mut overlay_cache).map(Some)
            });
            match parsed {
                Ok(None) => {}
                Ok(Some(job)) => jobs.push(Ok(job)),
                Err(e) => jobs.push(Err(format!("{}: record {}: {e}", path.display(), i + 1))),
            }
        }
        let mut builder = rayon::ThreadPoolBuilder::new();
        if let Some(n) = args.threads {
            builder = builder.num_threads(n);
        }
        let pool = builder.build().map_err(|e| format!("Rayon: {e}"))?;
        // Indexed parallel collect preserves CSV order. No mutable global RNG/market.
        let outcomes: Vec<Outcome> = pool.install(|| {
            jobs.par_iter()
                .map(|job| match job {
                    Ok(job) => Replay::new_with_overlays(
                        &config,
                        &job.a,
                        &job.b,
                        job.seed,
                        job.reverse,
                        trim_hands,
                        [job.overlays[0].as_deref(), job.overlays[1].as_deref()],
                    )
                    .run(),
                    Err(e) => Outcome::error(e),
                })
                .collect()
        });
        failed = outcomes.iter().any(|o| !o.errors.is_empty());
        for outcome in outcomes {
            write_json_line(&mut stdout, &outcome)?;
        }
    } else {
        let a = cache.load(args.tape_a.as_deref().expect("clap requires tape-a"))?;
        let b = cache.load(args.tape_b.as_deref().expect("clap requires tape-b"))?;
        let overlay_a = match args.overlay_a.as_deref() {
            Some(path) => overlay_cache.load_optional(path)?,
            None => None,
        };
        let overlay_b = match args.overlay_b.as_deref() {
            Some(path) => overlay_cache.load_optional(path)?,
            None => None,
        };
        let mut replay = Replay::new_with_overlays(
            &config,
            &a,
            &b,
            args.seed.expect("clap requires seed"),
            args.reverse_seats,
            trim_hands,
            [overlay_a.as_deref(), overlay_b.as_deref()],
        );
        if let Some(path) = &args.trace {
            let file = File::create(path).map_err(|e| format!("{}: {e}", path.display()))?;
            let mut trace = BufWriter::new(file);
            write_json_line(&mut trace, &replay.game.snapshot())?;
            while replay.advance() {
                write_json_line(&mut trace, &replay.game.snapshot())?;
            }
            trace.flush().map_err(|e| e.to_string())?;
        } else {
            while replay.advance() {}
        }
        let outcome = replay.outcome();
        failed = !outcome.errors.is_empty();
        write_json_line(&mut stdout, &outcome)?;
    }
    stdout.flush().map_err(|e| e.to_string())?;
    Ok(failed)
}

fn main() -> ExitCode {
    match execute(Args::parse()) {
        Ok(false) => ExitCode::SUCCESS,
        Ok(true) => ExitCode::FAILURE,
        Err(e) => {
            // Machine-readable failure; diagnostics never masquerade as successful rewards.
            let _ = write_json_line(&mut io::stdout().lock(), &Outcome::error(e));
            ExitCode::FAILURE
        }
    }
}
