//! Deterministic, tape-only Kaggriculture 1.32.7 simulation.
//! The board and inventories are fixed arrays; hand storage is reserved before
//! play. Separate games are parallelizable; seats in one game MUST stay coupled.

pub mod config;
pub mod data;
mod engine;
pub mod market;
pub mod overlay;
pub mod rng;
mod snapshot;
pub mod tape;

pub use config::Config;
pub use engine::Game;
pub use overlay::MarketOverlay;
use serde::Serialize;
pub use tape::Tape;

/// Immutable actions and per-seat allocation bounds, reusable across all seeds.
pub struct PreparedTape {
    tape: Tape,
    turns: usize,
    turns_per_day: usize,
    max_orders: usize,
    hand_capacities: [usize; 2],
}

impl PreparedTape {
    pub fn new(tape: Tape, config: &Config, turns: usize) -> Self {
        let hand_capacities = std::array::from_fn(|i| tape.hand_capacity(i, turns, config));
        Self {
            tape,
            turns,
            turns_per_day: config.turns_per_day,
            max_orders: config.max_market_orders,
            hand_capacities,
        }
    }
}

#[derive(Debug, Serialize, PartialEq)]
pub struct Outcome {
    /// Always in input tape A/B order, including reversed-seat games.
    pub rewards: Option<[f64; 2]>,
    pub errors: Vec<String>,
}

impl Outcome {
    pub fn error(message: impl Into<String>) -> Self {
        Self {
            rewards: None,
            errors: vec![message.into()],
        }
    }
}

pub struct Replay<'a> {
    pub game: Game<'a>,
    tapes: [&'a PreparedTape; 2],
    reverse: bool,
    trim_hands: [bool; 2],
    overlays: [Option<&'a MarketOverlay>; 2],
    turns: usize,
}

impl<'a> Replay<'a> {
    pub fn new(
        config: &'a Config,
        tape_a: &'a PreparedTape,
        tape_b: &'a PreparedTape,
        seed: i64,
        reverse: bool,
        trim_hands: bool,
    ) -> Self {
        Self::new_with_hand_trimming(config, tape_a, tape_b, seed, reverse, [trim_hands; 2])
    }

    /// Per-input-agent rules in A/B order, not physical-seat order. Reversing
    /// seats moves each rule with its tape; rewards still return in A/B order.
    pub fn new_with_hand_trimming(
        config: &'a Config,
        tape_a: &'a PreparedTape,
        tape_b: &'a PreparedTape,
        seed: i64,
        reverse: bool,
        trim_hands: [bool; 2],
    ) -> Self {
        Self::new_with_overlays(
            config, tape_a, tape_b, seed, reverse, trim_hands, [None, None],
        )
    }

    /// Overlay profiles are supplied in input A/B order and follow their tapes
    /// when physical seats are reversed.
    pub fn new_with_overlays(
        config: &'a Config,
        tape_a: &'a PreparedTape,
        tape_b: &'a PreparedTape,
        seed: i64,
        reverse: bool,
        trim_hands: [bool; 2],
        overlays: [Option<&'a MarketOverlay>; 2],
    ) -> Self {
        assert_eq!(
            tape_a.turns, tape_b.turns,
            "tapes must be prepared for the same number of turns"
        );
        for tape in [tape_a, tape_b] {
            assert_eq!(
                tape.turns_per_day, config.turns_per_day,
                "prepare tapes again after changing turnsPerDay"
            );
            assert_eq!(
                tape.max_orders, config.max_market_orders,
                "prepare tapes again after changing maxMarketOrdersPerTurn"
            );
        }
        let tapes = if reverse {
            [tape_b, tape_a]
        } else {
            [tape_a, tape_b]
        };
        let trim_hands = if reverse {
            [trim_hands[1], trim_hands[0]]
        } else {
            trim_hands
        };
        let overlays = if reverse {
            [overlays[1], overlays[0]]
        } else {
            overlays
        };
        let game = Game::new(
            config,
            seed,
            [tapes[0].hand_capacities[0], tapes[1].hand_capacities[1]],
        );
        Self {
            game,
            tapes,
            reverse,
            trim_hands,
            overlays,
            turns: tape_a.turns,
        }
    }

    /// Execute one turn, returning false once the requested horizon is reached.
    pub fn advance(&mut self) -> bool {
        let turn = self.game.turn();
        if turn >= self.turns {
            return false;
        }
        let sources = [
            self.tapes[0].tape.action(0, turn),
            self.tapes[1].tape.action(1, turn),
        ];
        let actions: [std::borrow::Cow<'_, tape::Action>; 2] =
            std::array::from_fn(|seat| match self.overlays[seat] {
                Some(profile) => std::borrow::Cow::Owned(profile.apply(&self.game, seat, sources[seat])),
                None => std::borrow::Cow::Borrowed(sources[seat]),
            });
        self.game.step_with_hand_trimming(
            [&actions[0], &actions[1]],
            self.trim_hands,
        );
        true
    }

    pub fn outcome(&self) -> Outcome {
        let mut rewards = self.game.rewards();
        if self.reverse {
            rewards.swap(0, 1);
        }
        if !rewards.iter().all(|v| v.is_finite()) {
            return Outcome::error(
                "non-finite money; configuration exceeds supported numeric range",
            );
        }
        let mut errors = Vec::new();
        let aborted = self.game.market_loop_aborts();
        if aborted > 0 {
            errors.push(format!(
                "market loop reached the Python 100k-iteration guard {aborted} time(s)"
            ));
        }
        Outcome {
            rewards: Some(rewards),
            errors,
        }
    }

    pub fn run(mut self) -> Outcome {
        while self.advance() {}
        self.outcome()
    }
}
