use serde_json::{Map, Value};
use crate::{data::{BOARD_SIZE, ITEM_NAMES, PRODUCT_COUNT}, market::{default_params, PriceCurve}};

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
        let root = input.get("configuration").unwrap_or(input).as_object()
            .ok_or("configuration must be a JSON object")?;
        let mut flat = Map::new();
        for (key, value) in root {
            flat.insert(key.clone(), value.get("default").unwrap_or(value).clone());
        }
        let integer = |name: &str, default: i64, min: i64| -> Result<i64, String> {
            let v = match flat.get(name) {
                Some(value) => value.as_i64().ok_or_else(|| format!("{name} must be an integer"))?,
                None => default,
            };
            if v < min { return Err(format!("{name} must be >= {min}")); }
            Ok(v)
        };
        let positive = |name: &str, default: i64| -> Result<usize, String> {
            // Bound arithmetic used for day/lifespan calculations on all platforms.
            let n = integer(name, default, 1)?;
            if n > i64::from(i32::MAX) { return Err(format!("{name} exceeds i32::MAX")); }
            Ok(n as usize)
        };
        if integer("boardSize", 10, 4)? != BOARD_SIZE as i64 {
            return Err("this fixed-array simulator supports boardSize=10 only".into());
        }
        let weed_chance = flat.get("weedSpawnChance").map_or(Some(0.005), Value::as_f64)
            .filter(|n| n.is_finite() && *n >= 0.0)
            .ok_or("weedSpawnChance must be finite and >= 0")?;
        let mut params = default_params();
        let mut has_overrides = false;
        if let Some(overrides) = flat.get("marketParams") {
            let overrides = overrides.as_object().ok_or("marketParams must be an object")?;
            has_overrides = !overrides.is_empty();
            for (item, patch) in overrides {
                if let (Some(base), Some(patch)) = (params.get_mut(item).and_then(Value::as_object_mut), patch.as_object()) {
                    for (k, v) in patch { base.insert(k.clone(), v.clone()); }
                }
            }
        }
        let curves = ITEM_NAMES[..PRODUCT_COUNT].iter()
            .map(|name| PriceCurve::from_json(&params[name]).map_err(|e| format!("marketParams.{name}: {e}")))
            .collect::<Result<Vec<_>, _>>()?.try_into().expect("nine products");
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
