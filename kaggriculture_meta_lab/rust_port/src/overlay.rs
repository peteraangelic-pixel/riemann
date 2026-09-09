//! Small state-dependent market policy layered over an immutable unit tape.
use crate::{
    data::Item,
    engine::Game,
    tape::{Action, OrderKind},
};
use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct MarketOverlay {
    pub enabled: bool,
    pub start_day: i64,
    pub buy_stop_day: i64,
    pub endgame_day: i64,
    pub cash_reserve: f64,
    pub sell_fraction_bp: u32,
    pub endgame_sell_fraction_bp: u32,
    pub wheat_reserve: i64,
    pub carrot_reserve: i64,
    pub tomato_reserve: i64,
    pub strawberry_reserve: i64,
    pub melon_reserve: i64,
    pub egg_reserve: i64,
    pub milk_reserve: i64,
    pub wool_reserve: i64,
    pub fertilizer_reserve: i64,
    pub min_wheat_price: f64,
    pub min_carrot_price: f64,
    pub min_tomato_price: f64,
    pub min_strawberry_price: f64,
    pub min_melon_price: f64,
    pub min_egg_price: f64,
    pub min_milk_price: f64,
    pub min_wool_price: f64,
    pub min_fertilizer_price: f64,
}

impl Default for MarketOverlay {
    fn default() -> Self {
        Self {
            enabled: false,
            start_day: 0,
            buy_stop_day: 30,
            endgame_day: 27,
            cash_reserve: 0.0,
            sell_fraction_bp: 10_000,
            endgame_sell_fraction_bp: 10_000,
            wheat_reserve: 0,
            carrot_reserve: 0,
            tomato_reserve: 0,
            strawberry_reserve: 0,
            melon_reserve: 0,
            egg_reserve: 0,
            milk_reserve: 0,
            wool_reserve: 0,
            fertilizer_reserve: 0,
            min_wheat_price: 0.0,
            min_carrot_price: 0.0,
            min_tomato_price: 0.0,
            min_strawberry_price: 0.0,
            min_melon_price: 0.0,
            min_egg_price: 0.0,
            min_milk_price: 0.0,
            min_wool_price: 0.0,
            min_fertilizer_price: 0.0,
        }
    }
}

impl MarketOverlay {
    pub fn from_json(value: &serde_json::Value) -> Result<Self, String> {
        let profile: Self = serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
        profile.validate()?;
        Ok(profile)
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.start_day < 0 || self.buy_stop_day < 0 || self.endgame_day < 0 {
            return Err("overlay days must be non-negative".into());
        }
        if self.sell_fraction_bp > 10_000 || self.endgame_sell_fraction_bp > 10_000 {
            return Err("overlay sell fractions must be in 0..=10000 basis points".into());
        }
        let prices = [
            self.cash_reserve,
            self.min_wheat_price,
            self.min_carrot_price,
            self.min_tomato_price,
            self.min_strawberry_price,
            self.min_melon_price,
            self.min_egg_price,
            self.min_milk_price,
            self.min_wool_price,
            self.min_fertilizer_price,
        ];
        if prices.iter().any(|v| !v.is_finite() || *v < 0.0) {
            return Err(
                "overlay money and price thresholds must be finite and non-negative".into(),
            );
        }
        if [
            self.wheat_reserve,
            self.carrot_reserve,
            self.tomato_reserve,
            self.strawberry_reserve,
            self.melon_reserve,
            self.egg_reserve,
            self.milk_reserve,
            self.wool_reserve,
            self.fertilizer_reserve,
        ]
        .iter()
        .any(|v| *v < 0)
        {
            return Err("overlay inventory reserves must be non-negative".into());
        }
        Ok(())
    }

    fn reserve(&self, item: Item) -> i64 {
        match item {
            Item::Wheat => self.wheat_reserve,
            Item::Carrot => self.carrot_reserve,
            Item::Tomato => self.tomato_reserve,
            Item::Strawberry => self.strawberry_reserve,
            Item::Melon => self.melon_reserve,
            Item::Egg => self.egg_reserve,
            Item::Milk => self.milk_reserve,
            Item::Wool => self.wool_reserve,
            Item::Fertilizer => self.fertilizer_reserve,
            _ => 0,
        }
    }

    fn min_price(&self, item: Item) -> f64 {
        match item {
            Item::Wheat => self.min_wheat_price,
            Item::Carrot => self.min_carrot_price,
            Item::Tomato => self.min_tomato_price,
            Item::Strawberry => self.min_strawberry_price,
            Item::Melon => self.min_melon_price,
            Item::Egg => self.min_egg_price,
            Item::Milk => self.min_milk_price,
            Item::Wool => self.min_wool_price,
            Item::Fertilizer => self.min_fertilizer_price,
            _ => 0.0,
        }
    }

    pub(crate) fn apply(&self, game: &Game<'_>, seat: usize, source: &Action) -> Action {
        let mut action = source.clone();
        let day = (game.turn / game.config.turns_per_day) as i64;
        if !self.enabled || day < self.start_day {
            return action;
        }
        let fraction = if day >= self.endgame_day {
            self.endgame_sell_fraction_bp
        } else {
            self.sell_fraction_bp
        } as u64;
        let farm = &game.farms[seat];
        for order in &mut action.market {
            match order.kind {
                OrderKind::Sell(item) => {
                    let quote =
                        game.config.curves[item.index()].price(game.market_inventory[item.index()]);
                    let available = (farm.shed[item.index()] - self.reserve(item)).max(0) as u64;
                    let allowed = available.saturating_mul(fraction) / 10_000;
                    order.remaining = order.remaining.min(allowed);
                    if quote < self.min_price(item) {
                        order.remaining = 0;
                    }
                }
                OrderKind::Hire
                | OrderKind::BuyLand
                | OrderKind::BuyProduct(_)
                | OrderKind::BuySeed(_)
                | OrderKind::BuyAnimal(_) => {
                    if day >= self.buy_stop_day || farm.money <= self.cash_reserve {
                        order.remaining = 0;
                    }
                }
                OrderKind::Noop => {}
            }
        }
        action
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{tape::Tape, Config};
    use serde_json::json;

    #[test]
    fn rejects_unsafe_ranges_and_unknown_fields() {
        assert!(MarketOverlay::from_json(&json!({"sell_fraction_bp": 10001})).is_err());
        assert!(MarketOverlay::from_json(&json!({"surprise": 1})).is_err());
    }

    #[test]
    fn disabled_overlay_is_identity() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[{"market":[["SELL","WHEAT",9]]}],[{}]])).unwrap();
        let action = &tape.seats[0][0];
        let game = Game::new(&cfg, 0, [0, 0]);
        let out = MarketOverlay::default().apply(&game, 0, action);
        assert_eq!(out.market[0].remaining, 9);
    }

    #[test]
    fn sale_uses_live_shed_reserve_fraction_and_quote() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[{"market":[["SELL","WHEAT",99]]}],[{}]])).unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.farms[0].shed[Item::Wheat.index()] = 20;
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "wheat_reserve": 4, "sell_fraction_bp": 5000
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 8);
    }

    #[test]
    fn buy_stop_preserves_slots_as_zero_remaining_orders() {
        let cfg = Config::default();
        let tape =
            Tape::from_json(&json!([[{"market":[["HIRE"],["BUY_SEED","WHEAT",9]]}],[{}]])).unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.turn = cfg.turns_per_day * 27;
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "buy_stop_day": 27
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 0);
        assert_eq!(out.market[1].remaining, 0);
    }
}
