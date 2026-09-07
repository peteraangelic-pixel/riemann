use kg_sim::{data::Item, rng::PythonRandom, Config};
use serde_json::Value;

#[test]
fn cpython_rng_fingerprints_cross_twists_and_64_bit_seed_overflow() {
    let vectors: Value = serde_json::from_str(include_str!("fixtures/conformance.json")).unwrap();
    for row in vectors["rng"].as_array().unwrap() {
        let seed = row["seed"].as_i64().unwrap();
        let day = row["day"].as_i64().unwrap();
        let mut rng = PythonRandom::for_day(seed, day);
        let mut hash = 14_695_981_039_346_656_037_u64;
        for _ in 0..5000 {
            hash = hash.wrapping_mul(1_099_511_628_211) ^ u64::from(rng.next_u32());
        }
        assert_eq!(
            hash,
            row["words_fnv64"].as_u64().unwrap(),
            "seed={seed} day={day}"
        );
        let mut rng = PythonRandom::for_day(seed, day);
        for pair in row["mixed_calls"].as_array().unwrap() {
            assert_eq!(
                rng.random().to_bits(),
                pair[0].as_f64().unwrap().to_bits(),
                "random(): seed={seed} day={day}"
            );
            assert_eq!(
                u64::from(rng.choice8()),
                pair[1].as_u64().unwrap(),
                "choice(): seed={seed} day={day}"
            );
        }
    }
}

#[test]
fn all_default_price_curves_match_270009_python_quotes() {
    let vectors: Value = serde_json::from_str(include_str!("fixtures/conformance.json")).unwrap();
    let cfg = Config::default();
    for row in vectors["prices"].as_array().unwrap() {
        let item = Item::parse(row["item"].as_str().unwrap()).unwrap();
        let mut hash = 14_695_981_039_346_656_037_u64;
        for inventory in -10000..20001 {
            hash = hash.wrapping_mul(1_099_511_628_211)
                ^ cfg.curves[item.index()].price(f64::from(inventory)) as u64;
        }
        assert_eq!(hash, row["fnv64"].as_u64().unwrap(), "product={item:?}");
    }
}
