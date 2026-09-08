use crate::{
    data::{BOARD_SIZE, ITEM_NAMES, PRODUCT_COUNT},
    market::{default_params, PriceCurve},
};
use serde_json::{Map, Value};

/// Validated configuration, shared immutably by all Rayon workers.
#[derive(Clone, Debug)]
pub struct Config {
    pub episode_steps: usize,
    pub starting_money: f64,
    pub max_market_orders: usize,
    pub turns_per_day: usize,
    pub shed_capacity: i64,
    pub weed_chance: f64,
    pub shop_unlock_interval: usize,
    pub shop_sell_interval: usize,
    pub center_sell_interval: usize,
    pub hire_multiplier: u64,
    pub curves: [PriceCurve; PRODUCT_COUNT],
    pub(crate) resolved_params: Option<Value>,
}

impl Default for Config {
    fn default() -> Self {
        Self::from_json(&Value::Object(Map::new())).expect("valid built-in configuration")
    }
}

impl Config {
    /// Accept either flat overrides or the supplied Kaggle specification JSON.
    /// Irrelevant framework fields (timeouts, seed, etc.) are not simulated.
    pub fn from_json(input: &Value) -> Result<Self, String> {
        let root = input
            .get("configuration")
            .unwrap_or(input)
            .as_object()
            .ok_or("configuration must be a JSON object")?;
        // Only a complete specification carries schema defaults. In a flat
        // configuration, `marketParams.default` is just an unknown product;
        // unwrapping it would silently discard the actual resource overrides.
        let specification = input.get("name").is_some() && input.get("configuration").is_some();
        let mut flat = Map::new();
        for (key, value) in root {
            let setting = if specification { value.get("default").unwrap_or(value) } else { value };
            flat.insert(key.clone(), setting.clone());
        }
        let integer = |name: &str, default: i64, min: i64| -> Result<i64, String> {
            let v = match flat.get(name) {
                Some(value) => value
                    .as_i64()
                    .or_else(|| {
                        // JSON Schema's integer type also accepts e.g. 24.0.
                        // Reject fractional/out-of-range floats, never saturate.
                        value.as_f64().filter(|n| {
                            n.is_finite() && n.fract() == 0.0
                                && *n >= i64::MIN as f64
                                && *n < -(i64::MIN as f64)
                        }).map(|n| n as i64)
                    })
                    .ok_or_else(|| format!("{name} must be an integer in the i64 range"))?,
                None => default,
            };
            if v < min {
                return Err(format!("{name} must be >= {min}"));
            }
            Ok(v)
        };
        let positive = |name: &str, default: i64| -> Result<usize, String> {
            // Bound arithmetic used for day/lifespan calculations on all platforms.
            let n = integer(name, default, 1)?;
            if n > i64::from(i32::MAX) {
                return Err(format!("{name} exceeds i32::MAX"));
            }
            Ok(n as usize)
        };
        if integer("boardSize", 10, 4)? != BOARD_SIZE as i64 {
            return Err("this fixed-array simulator supports boardSize=10 only".into());
        }
        let weed_chance = flat
            .get("weedSpawnChance")
            .map_or(Some(0.005), Value::as_f64)
            .filter(|n| n.is_finite() && *n >= 0.0)
            .ok_or("weedSpawnChance must be finite and >= 0")?;
        let mut params = default_params();
        let mut has_overrides = false;
        if let Some(overrides) = flat.get("marketParams") {
            let overrides = overrides
                .as_object()
                .ok_or("marketParams must be an object")?;
            has_overrides = !overrides.is_empty();
            for (item, patch) in overrides {
                if let (Some(base), Some(patch)) = (
                    params.get_mut(item).and_then(Value::as_object_mut),
                    patch.as_object(),
                ) {
                    for (k, v) in patch {
                        base.insert(k.clone(), v.clone());
                    }
                }
            }
        }
        let curves = ITEM_NAMES[..PRODUCT_COUNT]
            .iter()
            .map(|name| {
                PriceCurve::from_json(&params[name])
                    .map_err(|e| format!("marketParams.{name}: {e}"))
            })
            .collect::<Result<Vec<_>, _>>()?
            .try_into()
            .expect("nine products");
        Ok(Self {
            episode_steps: positive("episodeSteps", 720)?,
            starting_money: integer("startingMoney", 3000, 0)? as f64,
            max_market_orders: positive("maxMarketOrdersPerTurn", 10)?,
            turns_per_day: positive("turnsPerDay", 24)?,
            shed_capacity: integer("shedCapacity", 100, 1)?,
            weed_chance,
            shop_unlock_interval: positive("townShopUnlockInterval", 3)?,
            shop_sell_interval: positive("townShopSellInterval", 4)?,
            center_sell_interval: positive("townCenterSellInterval", 24)?,
            hire_multiplier: integer("farmHandCostMult", 1, 0)? as u64,
            curves,
            resolved_params: has_overrides.then_some(params),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn flat_market_default_key_is_not_a_schema_descriptor() {
        let values = json!({"marketParams": {
            "default": {"WHEAT": {"base": 900}},
            "WHEAT": {"base": 40}
        }});
        for input in [values.clone(), json!({"configuration": values})] {
            let cfg = Config::from_json(&input).unwrap();
            assert_eq!(cfg.curves[0].base, 40.0);
            assert!(cfg.resolved_params.as_ref().unwrap().get("default").is_none());
        }
    }

    #[test]
    fn unknown_override_preserves_the_reference_params_snapshot() {
        let cfg = Config::from_json(&json!({"marketParams": {"default": {}}})).unwrap();
        assert_eq!(cfg.curves[0].base, 25.0);
        assert!(cfg.resolved_params.is_some());
    }

    #[test]
    fn full_specification_schema_defaults_are_unwrapped() {
        let cfg = Config::from_json(&json!({
            "name": "kaggriculture",
            "configuration": {
                "startingMoney": {"type": "integer", "default": 5000},
                "marketParams": {"type": "object", "default": {"WHEAT": {"base": 40}}}
            }
        })).unwrap();
        assert_eq!(cfg.starting_money, 5000.0);
        assert_eq!(cfg.curves[0].base, 40.0);
    }

    #[test]
    fn integer_valued_json_floats_follow_schema_integer_semantics() {
        let cfg = Config::from_json(&json!({
            "boardSize": 10.0, "startingMoney": 5000.0, "episodeSteps": 720.0,
            "turnsPerDay": 6.0, "shedCapacity": 3.0, "farmHandCostMult": 0.0
        })).unwrap();
        assert_eq!(cfg.starting_money, 5000.0);
        assert_eq!(cfg.episode_steps, 720);
        assert_eq!(cfg.turns_per_day, 6);
        assert_eq!(cfg.shed_capacity, 3);
        assert_eq!(cfg.hire_multiplier, 0);
        for bad in [json!(3.5), json!(true), json!("3"), json!(9223372036854775808.0)] {
            assert!(Config::from_json(&json!({"startingMoney": bad})).is_err());
        }
        assert!(Config::from_json(&json!({"startingMoney": i64::MAX})).is_ok());
    }
}
