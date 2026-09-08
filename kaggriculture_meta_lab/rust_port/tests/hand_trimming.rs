use kg_sim::{Config, PreparedTape, Replay, Tape};
use serde_json::json;

fn phantom_tape(config: &Config) -> PreparedTape {
    let actions = json!([
        {"market": [["BUY_SEED", "WHEAT", 1]]},
        {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]]}
    ]);
    PreparedTape::new(
        Tape::from_json(&json!([actions, actions])).unwrap(),
        config,
        2,
    )
}

#[test]
fn hand_rules_follow_input_agents_when_physical_seats_reverse() {
    let cfg = Config::default();
    let tape = phantom_tape(&cfg);
    for flags in [[false, false], [true, false], [false, true], [true, true]] {
        for reverse in [false, true] {
            let mut replay = Replay::new_with_hand_trimming(&cfg, &tape, &tape, 7, reverse, flags);
            while replay.advance() {}
            let snapshot = replay.game.snapshot();
            for physical in 0..2 {
                let input = if reverse { 1 - physical } else { physical };
                let tile = &snapshot["farms"][physical]["tiles"][4][4];
                assert_eq!(
                    !tile.is_null(),
                    flags[input],
                    "reverse={reverse} input={input}"
                );
                assert_eq!(
                    snapshot["privates"][physical]["seeds"]["WHEAT"],
                    json!(i32::from(!flags[input]))
                );
            }
            assert_eq!(replay.outcome().rewards, Some([2990.0, 2990.0]));
        }
    }
}

#[test]
fn old_uniform_trimming_api_is_unchanged() {
    let cfg = Config::default();
    let tape = phantom_tape(&cfg);
    for trim in [false, true] {
        let mut old = Replay::new(&cfg, &tape, &tape, -17, true, trim);
        let mut explicit = Replay::new_with_hand_trimming(&cfg, &tape, &tape, -17, true, [trim; 2]);
        while old.advance() {}
        while explicit.advance() {}
        assert_eq!(old.game.snapshot(), explicit.game.snapshot());
        assert_eq!(old.outcome(), explicit.outcome());
    }
}
