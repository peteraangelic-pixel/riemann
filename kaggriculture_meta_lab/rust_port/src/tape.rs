//! JSON is parsed and normalized once, outside the simulation hot path.
use crate::{config::Config, data::Item};
use serde_json::Value;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum UnitAction {
    #[default]
    Pass,
    Move(i8, i8),
    Drop,
    Pickup(Item, i64),
    Place(Item, i64),
    Plant(Item),
    Water,
    Harvest,
    Fertilize,
    Dig,
    BuildCoop,
    BuildPasture,
    Feed,
    CollectFertilizer,
    Care,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum OrderKind {
    #[default]
    Noop,
    Hire,
    BuyLand,
    Sell(Item),
    BuyProduct(Item),
    BuySeed(Item),
    BuyAnimal(Item),
}

#[derive(Clone, Copy, Debug, Default)]
pub struct Order {
    pub kind: OrderKind,
    pub remaining: u64,
}

#[derive(Clone, Debug, Default)]
pub struct Action {
    pub farmer: UnitAction,
    pub hands: Vec<UnitAction>,
    pub market: Vec<Order>,
}

/// Non-list/unknown operations are no-ops, as in the interpreter.
/// Numeric order strings/floats/bools use Python int()-style truncation.
fn quantity(v: &Value) -> Option<i64> {
    match v {
        Value::Bool(b) => Some(i64::from(*b)),
        Value::Number(n) => n.as_i64().or_else(|| n.as_f64().map(|f| f as i64)),
        Value::String(s) => {
            let s = s.trim();
            let digits = s.strip_prefix(['+', '-']).unwrap_or(s);
            if digits.is_empty()
                || digits.starts_with('_')
                || digits.ends_with('_')
                || digits.contains("__")
                || !digits.chars().all(|c| c.is_ascii_digit() || c == '_')
            {
                return None;
            }
            // Very large positive counts cannot exceed the engine's 99,999-unit guard.
            let clean = s.replace('_', "");
            clean.parse::<i64>().ok().or_else(|| {
                Some(if s.starts_with('-') {
                    i64::MIN
                } else {
                    i64::MAX
                })
            })
        }
        _ => None,
    }
}

impl UnitAction {
    fn parse(value: &Value) -> Self {
        let Some(a) = value.as_array() else {
            return Self::Pass;
        };
        let Some(op) = a.first().and_then(Value::as_str) else {
            return Self::Pass;
        };
        let item = || a.get(1).and_then(Value::as_str).and_then(Item::parse);
        let n = || a.get(2).map_or(Some(1), quantity);
        match op {
            "NORTH" => Self::Move(0, -1),
            "SOUTH" => Self::Move(0, 1),
            "EAST" => Self::Move(1, 0),
            "WEST" => Self::Move(-1, 0),
            "DROP" => Self::Drop,
            "PICKUP" => item()
                .zip(n())
                .map_or(Self::Pass, |(i, n)| Self::Pickup(i, n)),
            "PLACE" => item()
                .zip(n())
                .map_or(Self::Pass, |(i, n)| Self::Place(i, n)),
            "PLANT" => item()
                .filter(|i| i.is_crop())
                .map_or(Self::Pass, Self::Plant),
            "WATER" => Self::Water,
            "HARVEST" => Self::Harvest,
            "FERTILIZE" => Self::Fertilize,
            "DIG" => Self::Dig,
            "BUILD_COOP" => Self::BuildCoop,
            "BUILD_PASTURE" => Self::BuildPasture,
            "FEED" => Self::Feed,
            "COLLECT_FERTILIZER" => Self::CollectFertilizer,
            "CARE" => Self::Care,
            _ => Self::Pass,
        }
    }
}

impl Order {
    fn parse(value: &Value) -> Self {
        let Some(a) = value.as_array() else {
            return Self::default();
        };
        let Some(op) = a.first().and_then(Value::as_str) else {
            return Self::default();
        };
        if op == "HIRE" {
            return Self {
                kind: OrderKind::Hire,
                remaining: 0,
            };
        }
        if op == "BUY_LAND" {
            return Self {
                kind: OrderKind::BuyLand,
                remaining: 0,
            };
        }
        let Some((item, n)) = a
            .get(1)
            .and_then(Value::as_str)
            .and_then(Item::parse)
            .zip(a.get(2).and_then(quantity).filter(|n| *n > 0))
        else {
            return Self::default();
        };
        let kind = match op {
            "SELL" if item.is_product() => OrderKind::Sell(item),
            "BUY_PRODUCT" if matches!(item, Item::Wheat | Item::Fertilizer) => {
                OrderKind::BuyProduct(item)
            }
            "BUY_SEED" if item.is_crop() => OrderKind::BuySeed(item),
            "BUY_ANIMAL" if item.is_animal() => OrderKind::BuyAnimal(item),
            _ => OrderKind::Noop,
        };
        Self {
            kind,
            remaining: (n as u64).min(100_000),
        }
    }
}

impl Action {
    fn parse(value: &Value) -> Self {
        Self {
            farmer: value
                .get("farmer")
                .map_or(UnitAction::Pass, UnitAction::parse),
            hands: value
                .get("hands")
                .and_then(Value::as_array)
                .map(|a| a.iter().map(UnitAction::parse).collect())
                .unwrap_or_default(),
            // Preserve invalid order slots. Filtering them would change lockstep pairing.
            market: value
                .get("market")
                .and_then(Value::as_array)
                .map(|a| a.iter().map(Order::parse).collect())
                .unwrap_or_default(),
        }
    }
}

#[derive(Debug)]
pub struct Tape {
    pub seats: [Vec<Action>; 2],
}

impl Tape {
    pub fn from_json(value: &Value) -> Result<Self, String> {
        let seats = value.as_array().filter(|s| s.len() == 2).ok_or(
            "tape must be a JSON array [seat0_actions, seat1_actions] with exactly two seats",
        )?;
        let parse_seat = |seat: usize| -> Result<Vec<Action>, String> {
            let actions = seats[seat]
                .as_array()
                .filter(|s| !s.is_empty())
                .ok_or_else(|| format!("tape seat {seat} must be a nonempty action list"))?;
            Ok(actions.iter().map(Action::parse).collect())
        };
        Ok(Self {
            seats: [parse_seat(0)?, parse_seat(1)?],
        })
    }

    /// Repeat the last entry beyond a tape's length, matching the example's clamp.
    pub fn action(&self, seat: usize, turn: usize) -> &Action {
        let actions = &self.seats[seat];
        &actions[turn.min(actions.len() - 1)]
    }

    /// Exact upper bound on successful daily hires, computed before any turn.
    /// Allows free hiring and configuration overrides without a hard hand-count cap.
    pub fn hand_capacity(&self, seat: usize, turns: usize, cfg: &Config) -> usize {
        let (mut max, mut today) = (0, 0);
        for turn in 0..turns {
            if turn % cfg.turns_per_day == 0 {
                today = 0;
            }
            today += self
                .action(seat, turn)
                .market
                .iter()
                .take(cfg.max_market_orders)
                .filter(|o| o.kind == OrderKind::Hire)
                .count();
            max = max.max(today);
        }
        max
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn python_quantities_and_preserved_slots() {
        assert_eq!(quantity(&json!(" +1_2 ")), Some(12));
        assert_eq!(quantity(&json!("1__2")), None);
        assert_eq!(quantity(&json!("_2")), None);
        assert_eq!(quantity(&json!("3.2")), None);
        assert_eq!(quantity(&json!(3.9)), Some(3));
        assert_eq!(quantity(&json!(true)), Some(1));
        let a = Action::parse(&json!({"market": [[], ["HIRE"], ["SELL", "WHEAT", "2"]]}));
        assert_eq!(a.market.len(), 3);
        assert_eq!(a.market[1].kind, OrderKind::Hire);
    }
}
