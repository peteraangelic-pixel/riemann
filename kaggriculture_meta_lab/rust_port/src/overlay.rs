//! Small state-dependent market policy layered over an immutable unit tape.
use crate::{
    data::{Item, ACCESS, BOARD_SIZE, ITEM_COUNT},
    engine::{Farm, Game, Tile},
    tape::{Action, Order, OrderKind, UnitAction},
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
    // Generation-3 structural caps. Zero keeps the legacy identity behavior.
    pub hands_per_quadrant: u32,
    pub hand_buffer: u32,
    pub max_quadrants: u32,
    pub land_min_hands: u32,
    pub cow_target: i64,
    pub sheep_target: i64,
    pub goose_target: i64,
    pub animal_response_bp: u32,
    pub wheat_seed_target: i64,
    pub carrot_seed_target: i64,
    pub tomato_seed_target: i64,
    pub strawberry_seed_target: i64,
    pub melon_seed_target: i64,
    pub wheat_stock_target: i64,
    pub fertilizer_stock_target: i64,
    // V8 turn-1 opening selector. When enabled, replace the V7 wheat prefix
    // with the conservative V6 order if the post-turn-0 public fingerprint
    // falls inside all nonzero bounds.
    pub opening_switch_enabled: bool,
    pub opening_opponent_money_below: f64,
    pub opening_opponent_money_above: f64,
    pub opening_wheat_inventory_below: f64,
    pub opening_wheat_inventory_above: f64,
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
            hands_per_quadrant: 0,
            hand_buffer: 0,
            max_quadrants: 0,
            land_min_hands: 0,
            cow_target: 0,
            sheep_target: 0,
            goose_target: 0,
            animal_response_bp: 0,
            wheat_seed_target: 0,
            carrot_seed_target: 0,
            tomato_seed_target: 0,
            strawberry_seed_target: 0,
            melon_seed_target: 0,
            wheat_stock_target: 0,
            fertilizer_stock_target: 0,
            opening_switch_enabled: false,
            opening_opponent_money_below: 0.0,
            opening_opponent_money_above: 0.0,
            opening_wheat_inventory_below: 0.0,
            opening_wheat_inventory_above: 0.0,
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
            self.opening_opponent_money_below,
            self.opening_opponent_money_above,
            self.opening_wheat_inventory_below,
            self.opening_wheat_inventory_above,
        ];
        if prices.iter().any(|v| !v.is_finite() || *v < 0.0) {
            return Err(
                "overlay money and price thresholds must be finite and non-negative".into(),
            );
        }
        if self.max_quadrants > 4 {
            return Err("max_quadrants must be zero or at most four".into());
        }
        if self.animal_response_bp > 20_000 {
            return Err("animal_response_bp must be in 0..=20000".into());
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
            self.cow_target,
            self.sheep_target,
            self.goose_target,
            self.wheat_seed_target,
            self.carrot_seed_target,
            self.tomato_seed_target,
            self.strawberry_seed_target,
            self.melon_seed_target,
            self.wheat_stock_target,
            self.fertilizer_stock_target,
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

    /// Project only unit operations that change the shed before market orders.
    /// Unit actions execute farmer-first, then live hands, before the market.
    fn projected_shed(&self, game: &Game<'_>, seat: usize, source: &Action) -> [i64; ITEM_COUNT] {
        let farm = &game.farms[seat];
        let mut shed = farm.shed;
        let mut total = farm.shed_total;
        let actions = std::iter::once(source.farmer).chain(source.hands.iter().copied());
        for (unit, action) in farm.units.iter().zip(actions) {
            let adjacent = ACCESS.contains(&unit.pos);
            if !adjacent {
                continue;
            }
            match action {
                UnitAction::Pickup(item, n) if n > 0 => {
                    let take = n.min(shed[item.index()]);
                    shed[item.index()] -= take;
                    total -= take;
                }
                UnitAction::Place(item, n) if n > 0 => {
                    let tile = &farm.tiles
                        [usize::from(unit.pos[1]) * BOARD_SIZE + usize::from(unit.pos[0])];
                    if item.is_animal()
                        && matches!(tile, Tile::Structure(s) if *s == item.animal().structure)
                    {
                        continue;
                    }
                    let take = n
                        .min(unit.inventory.amounts[item.index()])
                        .min((game.config.shed_capacity - total).max(0));
                    shed[item.index()] += take;
                    total += take;
                }
                UnitAction::Drop => {
                    for &item in &unit.inventory.order[..unit.inventory.len] {
                        let take = unit.inventory.amounts[item.index()]
                            .min((game.config.shed_capacity - total).max(0));
                        shed[item.index()] += take;
                        total += take;
                    }
                }
                _ => {}
            }
        }
        shed
    }

    fn animal_target(&self, item: Item) -> i64 {
        match item {
            Item::Cow => self.cow_target,
            Item::Sheep => self.sheep_target,
            Item::Goose => self.goose_target,
            _ => 0,
        }
    }

    fn seed_target(&self, item: Item) -> i64 {
        match item {
            Item::Wheat => self.wheat_seed_target,
            Item::Carrot => self.carrot_seed_target,
            Item::Tomato => self.tomato_seed_target,
            Item::Strawberry => self.strawberry_seed_target,
            Item::Melon => self.melon_seed_target,
            _ => 0,
        }
    }

    fn placed_animals(farm: &Farm, item: Item) -> i64 {
        farm.tiles
            .iter()
            .filter(|tile| matches!(tile, Tile::Animal(animal) if animal.animal == item))
            .count() as i64
    }

    fn planted_crops(farm: &Farm, item: Item) -> i64 {
        farm.tiles
            .iter()
            .filter(|tile| matches!(tile, Tile::Plant(plant) if plant.crop == item))
            .count() as i64
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
        let opponent = &game.farms[1 - seat];
        if self.opening_switch_enabled && game.turn == 1 {
            let wheat_inventory = game.market_inventory[Item::Wheat.index()];
            let inside = (self.opening_opponent_money_below == 0.0
                || opponent.money <= self.opening_opponent_money_below)
                && (self.opening_opponent_money_above == 0.0
                    || opponent.money >= self.opening_opponent_money_above)
                && (self.opening_wheat_inventory_below == 0.0
                    || wheat_inventory <= self.opening_wheat_inventory_below)
                && (self.opening_wheat_inventory_above == 0.0
                    || wheat_inventory >= self.opening_wheat_inventory_above);
            if inside {
                action.market.clear();
                action.market.push(Order {
                    kind: OrderKind::Sell(Item::Wheat),
                    remaining: 13,
                });
                action.market.extend(source.market.iter().skip(2).copied());
            }
        }
        let projected_shed = self.projected_shed(game, seat, &action);
        let mut sale_budget: [u64; ITEM_COUNT] = std::array::from_fn(|i| {
            let item = crate::data::ITEMS[i];
            let available = (projected_shed[i] - self.reserve(item)).max(0) as u64;
            available.saturating_mul(fraction) / 10_000
        });
        let mut animal_budget = [u64::MAX; ITEM_COUNT];
        for item in [Item::Cow, Item::Sheep, Item::Goose] {
            let base = self.animal_target(item);
            if base > 0 {
                let response = Self::placed_animals(opponent, item)
                    .saturating_mul(i64::from(self.animal_response_bp))
                    / 10_000;
                let owned = projected_shed[item.index()] + Self::placed_animals(farm, item);
                animal_budget[item.index()] = (base + response - owned).max(0) as u64;
            }
        }
        let mut seed_budget = [u64::MAX; ITEM_COUNT];
        for item in [
            Item::Wheat,
            Item::Carrot,
            Item::Tomato,
            Item::Strawberry,
            Item::Melon,
        ] {
            let target = self.seed_target(item);
            if target > 0 {
                let owned = farm.seeds[item.index()] + Self::planted_crops(farm, item);
                seed_budget[item.index()] = (target - owned).max(0) as u64;
            }
        }
        let mut product_budget = [u64::MAX; ITEM_COUNT];
        for (item, target) in [
            (Item::Wheat, self.wheat_stock_target),
            (Item::Fertilizer, self.fertilizer_stock_target),
        ] {
            if target > 0 {
                product_budget[item.index()] =
                    (target - projected_shed[item.index()]).max(0) as u64;
            }
        }
        for order in &mut action.market {
            match order.kind {
                OrderKind::Sell(item) => {
                    let reserve = self.reserve(item);
                    let min_price = self.min_price(item);
                    if fraction == 10_000 && reserve == 0 && min_price == 0.0 {
                        continue;
                    }
                    let quote =
                        game.config.curves[item.index()].price(game.market_inventory[item.index()]);
                    if quote < min_price {
                        order.remaining = 0;
                    } else {
                        order.remaining = order.remaining.min(sale_budget[item.index()]);
                        sale_budget[item.index()] -= order.remaining;
                    }
                }
                OrderKind::Hire => {
                    let hands = farm.units.len().saturating_sub(1) as u32;
                    let labor_cap = self
                        .hands_per_quadrant
                        .saturating_mul(farm.unlocked as u32)
                        .saturating_add(self.hand_buffer);
                    if day >= self.buy_stop_day
                        || farm.money <= self.cash_reserve
                        || (self.hands_per_quadrant > 0 && hands >= labor_cap)
                    {
                        order.remaining = 0;
                    }
                }
                OrderKind::BuyLand => {
                    let hands = farm.units.len().saturating_sub(1) as u32;
                    if day >= self.buy_stop_day
                        || farm.money <= self.cash_reserve
                        || (self.max_quadrants > 0 && farm.unlocked as u32 >= self.max_quadrants)
                        || (self.land_min_hands > 0 && hands < self.land_min_hands)
                    {
                        order.remaining = 0;
                    }
                }
                OrderKind::BuyProduct(item) => {
                    if day >= self.buy_stop_day || farm.money <= self.cash_reserve {
                        order.remaining = 0;
                    } else if product_budget[item.index()] != u64::MAX {
                        order.remaining = order.remaining.min(product_budget[item.index()]);
                        product_budget[item.index()] -= order.remaining;
                    }
                }
                OrderKind::BuySeed(item) => {
                    if day >= self.buy_stop_day || farm.money <= self.cash_reserve {
                        order.remaining = 0;
                    } else if seed_budget[item.index()] != u64::MAX {
                        order.remaining = order.remaining.min(seed_budget[item.index()]);
                        seed_budget[item.index()] -= order.remaining;
                    }
                }
                OrderKind::BuyAnimal(item) => {
                    if day >= self.buy_stop_day || farm.money <= self.cash_reserve {
                        order.remaining = 0;
                    } else if animal_budget[item.index()] != u64::MAX {
                        order.remaining = order.remaining.min(animal_budget[item.index()]);
                        animal_budget[item.index()] -= order.remaining;
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
    fn turn_one_switch_uses_public_fingerprint_and_preserves_tail() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"market":[["BUY_PRODUCT","WHEAT",60],["SELL","WHEAT",90],["BUY_PRODUCT","WHEAT",5],["HIRE"]]}
        ],[{}]])).unwrap();
        let source = &tape.seats[0][0];
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.turn = 1;
        game.farms[1].money = 2500.0;
        game.market_inventory[Item::Wheat.index()] = 9973.0;
        let profile = MarketOverlay::from_json(&json!({
            "enabled":true,
            "opening_switch_enabled":true,
            "opening_opponent_money_below":2600,
            "opening_wheat_inventory_below":9980
        }))
        .unwrap();
        let switched = profile.apply(&game, 0, source);
        assert_eq!(switched.market.len(), 3);
        assert_eq!(switched.market[0].kind, OrderKind::Sell(Item::Wheat));
        assert_eq!(switched.market[0].remaining, 13);
        assert_eq!(switched.market[1].kind, OrderKind::BuyProduct(Item::Wheat));
        assert_eq!(switched.market[2].kind, OrderKind::Hire);
        game.farms[1].money = 2700.0;
        let unchanged = profile.apply(&game, 0, source);
        assert_eq!(unchanged.market.len(), 4);
        assert_eq!(unchanged.market[0].kind, OrderKind::BuyProduct(Item::Wheat));
        assert_eq!(unchanged.market[0].remaining, 60);
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
    fn enabled_defaults_are_identity_for_buy_then_sell() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"market":[["BUY_PRODUCT","WHEAT",13],["SELL","WHEAT",13]]}
        ],[{}]]))
        .unwrap();
        let game = Game::new(&cfg, 0, [0, 0]);
        let profile = MarketOverlay::from_json(&json!({"enabled": true})).unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 13);
        assert_eq!(out.market[1].remaining, 13);
    }

    #[test]
    fn structural_caps_share_cumulative_budgets() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"market":[
                ["BUY_ANIMAL","COW",9],["BUY_ANIMAL","COW",9],
                ["BUY_SEED","WHEAT",20],["BUY_SEED","WHEAT",20],
                ["BUY_PRODUCT","FERTILIZER",8],["BUY_PRODUCT","FERTILIZER",8]
            ]}
        ],[{}]]))
        .unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.farms[0].shed[Item::Cow.index()] = 2;
        game.farms[0].seeds[Item::Wheat.index()] = 3;
        game.farms[0].shed[Item::Fertilizer.index()] = 1;
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "cow_target": 5, "wheat_seed_target": 8,
            "fertilizer_stock_target": 4
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!([out.market[0].remaining, out.market[1].remaining], [3, 0]);
        assert_eq!([out.market[2].remaining, out.market[3].remaining], [5, 0]);
        assert_eq!([out.market[4].remaining, out.market[5].remaining], [3, 0]);
    }

    #[test]
    fn structural_zero_defaults_remain_identity() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"market":[["HIRE"],["BUY_LAND"],["BUY_ANIMAL","COW",17],
                       ["BUY_SEED","WHEAT",19],["BUY_PRODUCT","WHEAT",23]]}
        ],[{}]]))
        .unwrap();
        let game = Game::new(&cfg, 0, [0, 0]);
        let profile = MarketOverlay::from_json(&json!({"enabled": true})).unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert!(matches!(out.market[0].kind, OrderKind::Hire));
        assert!(matches!(out.market[1].kind, OrderKind::BuyLand));
        assert_eq!(
            out.market
                .iter()
                .map(|order| order.remaining)
                .collect::<Vec<_>>(),
            vec![0, 0, 17, 19, 23]
        );
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
    fn sale_fraction_is_one_budget_across_repeated_orders() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"market":[["SELL","WHEAT",9],["SELL","WHEAT",9]]}
        ],[{}]]))
        .unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.farms[0].shed[Item::Wheat.index()] = 20;
        game.farms[0].shed_total = 20;
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "sell_fraction_bp": 5000
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 9);
        assert_eq!(out.market[1].remaining, 1);
    }

    #[test]
    fn same_turn_drop_is_saleable_before_market() {
        let cfg = Config::default();
        let tape = Tape::from_json(&json!([[
            {"farmer":["DROP"],"market":[["SELL","WHEAT",99]]}
        ],[{}]]))
        .unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.farms[0].units[0].inventory.add(Item::Wheat, 6);
        let profile = MarketOverlay::from_json(&json!({
            "enabled": true, "min_wheat_price": 1
        }))
        .unwrap();
        let out = profile.apply(&game, 0, &tape.seats[0][0]);
        assert_eq!(out.market[0].remaining, 6);
        game.step([&out, &tape.seats[1][0]], false);
        assert_eq!(game.farms[0].shed[Item::Wheat.index()], 0);
        assert!(game.farms[0].money > cfg.starting_money);
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
