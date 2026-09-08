// Rust reimplementation of the Kaggriculture 1.32.7 interpreter (Apache-2.0).
// See reference/kaggriculture_sim.py for the unmodified authoritative rules.
use crate::{
    config::Config,
    data::*,
    rng::PythonRandom,
    tape::{Action, Order, OrderKind, UnitAction},
};

/// Small insertion-ordered inventory. Python dict order decides which goods
/// survive shed overflow. A plain item-index array alone is NOT equivalent.
#[derive(Clone, Debug)]
pub(crate) struct Inventory {
    pub amounts: [i64; ITEM_COUNT],
    pub order: [Item; ITEM_COUNT],
    pub len: usize,
}

impl Default for Inventory {
    fn default() -> Self {
        Self {
            amounts: [0; ITEM_COUNT],
            order: [Item::Wheat; ITEM_COUNT],
            len: 0,
        }
    }
}

impl Inventory {
    pub fn add(&mut self, item: Item, n: i64) {
        debug_assert!(n > 0);
        let i = item.index();
        if self.amounts[i] == 0 {
            self.order[self.len] = item;
            self.len += 1;
        }
        self.amounts[i] += n;
    }

    pub fn take(&mut self, item: Item, n: i64) -> bool {
        let i = item.index();
        if self.amounts[i] < n {
            return false;
        }
        self.amounts[i] -= n;
        if self.amounts[i] == 0 {
            let pos = self.order[..self.len]
                .iter()
                .position(|&v| v == item)
                .expect("inventory invariant");
            self.order.copy_within(pos + 1..self.len, pos);
            self.len -= 1;
        }
        true
    }

    fn drop_to_shed(&mut self, shed: &mut [i64; ITEM_COUNT], total: &mut i64, capacity: i64) {
        for &item in &self.order[..self.len] {
            let i = item.index();
            let take = self.amounts[i].min((capacity - *total).max(0));
            shed[i] += take;
            *total += take;
            self.amounts[i] = 0; // Overflow is discarded, not retained.
        }
        self.len = 0;
    }
}

#[derive(Clone, Debug)]
pub(crate) struct Unit {
    pub pos: [u8; 2],
    pub inventory: Inventory,
}

impl Unit {
    fn new(pos: [u8; 2]) -> Self {
        Self {
            pos,
            inventory: Inventory::default(),
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct Plant {
    pub crop: Item,
    pub planted_day: i64,
    pub watered_today: bool,
    pub consecutive_unwatered: u8,
    pub yield_units: i32,
    pub max_lifespan_step: i64,
    pub fertilized_until_day: i64,
}

impl Plant {
    fn new(crop: Item, day: i64, turns_per_day: usize) -> Self {
        let cd = crop.crop();
        Self {
            crop,
            planted_day: day,
            watered_today: false,
            consecutive_unwatered: 1,
            yield_units: i32::from(!cd.ongoing),
            max_lifespan_step: if cd.ongoing {
                -1
            } else {
                (day + cd.max_yield_day + 1) * turns_per_day as i64
            },
            fertilized_until_day: -1,
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct Animal {
    pub animal: Item,
    pub placed_day: i64,
    pub yield_units: i32,
    pub consecutive_unfed: u8,
    pub fed_today: bool,
    pub cared_today: bool,
    pub fertilizer_available: bool,
    pub pending_care_bonus: i32,
}

impl Animal {
    fn new(animal: Item, day: i64) -> Self {
        Self {
            animal,
            placed_day: day,
            yield_units: 0,
            consecutive_unfed: 0,
            fed_today: false,
            cared_today: false,
            fertilizer_available: false,
            pending_care_bonus: 0,
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub(crate) enum Tile {
    Empty,
    Locked,
    Weed,
    Structure(Structure),
    Plant(Plant),
    Animal(Animal),
}

#[derive(Debug)]
pub(crate) struct Farm {
    pub money: f64,
    pub tiles: [Tile; TILE_COUNT],
    pub units: Vec<Unit>,
    pub unlocked: usize,
    pub shed: [i64; ITEM_COUNT],
    pub shed_total: i64,
    pub seeds: [i64; CROP_COUNT],
    hire_fib: [u128; 2],
}

impl Farm {
    fn new(cfg: &Config, hand_capacity: usize) -> Self {
        // Only this setup allocates. Hires push within the proven tape bound.
        let mut units = Vec::with_capacity(hand_capacity + 1);
        units.push(Unit::new(ACCESS[0]));
        Self {
            money: cfg.starting_money,
            tiles: std::array::from_fn(|i| {
                if quadrant(i % BOARD_SIZE, i / BOARD_SIZE) == 0 {
                    Tile::Empty
                } else {
                    Tile::Locked
                }
            }),
            units,
            unlocked: 1,
            shed: [0; ITEM_COUNT],
            shed_total: 0,
            seeds: [0; CROP_COUNT],
            hire_fib: [1, 1],
        }
    }

    fn apply_actions(&mut self, action: &Action, cfg: &Config, day: i64, trim_hands: bool) {
        let count = if trim_hands {
            action.hands.len().min(self.units.len() - 1)
        } else {
            action.hands.len()
        };
        let hands = &action.hands[..count];
        let mut demand = [0_usize; CROP_COUNT];
        for a in std::iter::once(&action.farmer).chain(hands) {
            if let UnitAction::Plant(item) = a {
                demand[item.index()] += 1;
            }
        }
        let blocked: [bool; CROP_COUNT] =
            std::array::from_fn(|i| demand[i] as u64 > self.seeds[i] as u64);
        let allowed =
            |a: UnitAction| !matches!(a, UnitAction::Plant(item) if blocked[item.index()]);
        if allowed(action.farmer) {
            self.apply_unit(0, action.farmer, cfg, day);
        }
        // In raw mode nonexistent hands still contributed to demand above.
        for (i, &a) in hands.iter().take(self.units.len() - 1).enumerate() {
            if allowed(a) {
                self.apply_unit(i + 1, a, cfg, day);
            }
        }
    }

    fn apply_unit(&mut self, idx: usize, action: UnitAction, cfg: &Config, day: i64) {
        let unit = &mut self.units[idx];
        if let UnitAction::Move(dx, dy) = action {
            let nx = i16::from(unit.pos[0]) + i16::from(dx);
            let ny = i16::from(unit.pos[1]) + i16::from(dy);
            if nx >= 0 && nx < BOARD_SIZE as i16 && ny >= 0 && ny < BOARD_SIZE as i16 {
                // Movement on LOCKED tiles is allowed, including hand spawns.
                unit.pos = [nx as u8, ny as u8];
            }
            return;
        }
        if action == UnitAction::Pass {
            return;
        }
        let adjacent = ACCESS.contains(&unit.pos);
        let tile =
            &mut self.tiles[usize::from(unit.pos[1]) * BOARD_SIZE + usize::from(unit.pos[0])];
        let inv = &mut unit.inventory;
        match action {
            UnitAction::Drop => {
                if adjacent {
                    inv.drop_to_shed(&mut self.shed, &mut self.shed_total, cfg.shed_capacity);
                }
                return;
            }
            UnitAction::Pickup(item, n) => {
                if adjacent && n > 0 {
                    let n = n.min(self.shed[item.index()]);
                    if n > 0 {
                        self.shed[item.index()] -= n;
                        self.shed_total -= n;
                        inv.add(item, n);
                    }
                }
                return;
            }
            UnitAction::Place(item, n) => {
                if item.is_animal()
                    && matches!(tile, Tile::Structure(s) if *s == item.animal().structure)
                {
                    if inv.take(item, 1) {
                        *tile = Tile::Animal(Animal::new(item, day));
                    }
                    return; // On a matching structure, do not fall through to shed drop.
                }
                if adjacent && n > 0 {
                    let n = n
                        .min(inv.amounts[item.index()])
                        .min((cfg.shed_capacity - self.shed_total).max(0));
                    if n > 0 && inv.take(item, n) {
                        self.shed[item.index()] += n;
                        self.shed_total += n;
                    }
                }
                return;
            }
            _ => {}
        }
        if matches!(tile, Tile::Locked) {
            return;
        }
        match action {
            UnitAction::Plant(crop)
                if matches!(tile, Tile::Empty) && self.seeds[crop.index()] > 0 =>
            {
                self.seeds[crop.index()] -= 1;
                *tile = Tile::Plant(Plant::new(crop, day, cfg.turns_per_day));
            }
            UnitAction::Water => {
                if let Tile::Plant(p) = tile {
                    if p.watered_today {
                        return;
                    }
                    p.watered_today = true;
                    let cd = p.crop.crop();
                    let age = day - p.planted_day;
                    if !cd.ongoing && (cd.max_yield_day + 1) / 2 <= age && age <= cd.max_yield_day {
                        let bonus = if p.fertilized_until_day >= day { 2 } else { 1 };
                        p.yield_units = cd.max_yield.min(p.yield_units + bonus);
                    }
                }
            }
            UnitAction::Harvest => match tile {
                Tile::Plant(p) if p.yield_units > 0 => {
                    let cd = p.crop.crop();
                    if day - p.planted_day < cd.first_yield_day {
                        return;
                    }
                    inv.add(p.crop, i64::from(p.yield_units));
                    p.yield_units = 0;
                    if !cd.ongoing {
                        *tile = Tile::Empty;
                    }
                }
                Tile::Animal(a) if a.yield_units > 0 => {
                    inv.add(a.animal.animal().product, i64::from(a.yield_units));
                    a.yield_units = 0;
                }
                _ => {}
            },
            UnitAction::Fertilize => {
                if let Tile::Plant(p) = tile {
                    if inv.take(Item::Fertilizer, 1) {
                        p.fertilized_until_day = p.fertilized_until_day.max(day + 2);
                    }
                }
            }
            UnitAction::Dig if !matches!(tile, Tile::Animal(_)) => *tile = Tile::Empty,
            UnitAction::BuildCoop if matches!(tile, Tile::Empty) => {
                *tile = Tile::Structure(Structure::Coop)
            }
            UnitAction::BuildPasture if matches!(tile, Tile::Empty) => {
                *tile = Tile::Structure(Structure::Pasture)
            }
            UnitAction::Feed => {
                if let Tile::Animal(a) = tile {
                    if !a.fed_today && inv.take(Item::Wheat, 1) {
                        a.fed_today = true;
                    }
                }
            }
            UnitAction::CollectFertilizer => {
                if let Tile::Animal(a) = tile {
                    if a.fertilizer_available {
                        a.fertilizer_available = false;
                        inv.add(Item::Fertilizer, 1);
                    }
                }
            }
            UnitAction::Care => {
                if let Tile::Animal(a) = tile {
                    a.cared_today = true;
                }
            }
            _ => {}
        }
    }

    fn hire(&mut self, cfg: &Config) {
        let cost = self.hire_fib[0].saturating_mul(u128::from(cfg.hire_multiplier));
        if (self.money as u128) < cost {
            return;
        }
        self.money -= cost as f64;
        self.hire_fib = [
            self.hire_fib[1],
            self.hire_fib[0].saturating_add(self.hire_fib[1]),
        ];
        let mut occupancy = [0_usize; 4];
        for unit in &self.units {
            if let Some(i) = ACCESS.iter().position(|&p| p == unit.pos) {
                occupancy[i] += 1;
            }
        }
        let best = (0..4)
            .min_by_key(|&i| occupancy[i])
            .expect("four access tiles");
        // A bad caller-provided bound must not silently introduce an allocation.
        assert!(
            self.units.len() < self.units.capacity(),
            "insufficient preallocated hand capacity"
        );
        self.units.push(Unit::new(ACCESS[best]));
    }

    fn buy_land(&mut self) {
        if self.unlocked >= 4 || self.money < LAND_PRICES[self.unlocked - 1] {
            return;
        }
        self.money -= LAND_PRICES[self.unlocked - 1];
        let q = self.unlocked;
        self.unlocked += 1;
        for (i, tile) in self.tiles.iter_mut().enumerate() {
            if quadrant(i % BOARD_SIZE, i / BOARD_SIZE) == q && matches!(tile, Tile::Locked) {
                *tile = Tile::Empty;
            }
        }
    }

    fn commit(
        &mut self,
        kind: OrderKind,
        price: f64,
        inventory: &mut [f64; PRODUCT_COUNT],
        cfg: &Config,
    ) -> bool {
        match kind {
            OrderKind::Sell(item) => {
                if self.shed[item.index()] <= 0 {
                    return false;
                }
                self.shed[item.index()] -= 1;
                self.shed_total -= 1;
                self.money += price;
                // Floor-price sales DO NOT increase supply.
                if price > 1.0 {
                    inventory[item.index()] += 1.0;
                }
            }
            OrderKind::BuyProduct(item) => {
                if self.money < price || self.shed_total >= cfg.shed_capacity {
                    return false;
                }
                self.money -= price;
                self.shed[item.index()] += 1;
                self.shed_total += 1;
                inventory[item.index()] -= 1.0;
            }
            OrderKind::BuySeed(item) => {
                if self.money < price {
                    return false;
                }
                self.money -= price;
                self.seeds[item.index()] += 1;
            }
            OrderKind::BuyAnimal(item) => {
                if self.money < price || self.shed_total >= cfg.shed_capacity {
                    return false;
                }
                self.money -= price;
                self.shed[item.index()] += 1;
                self.shed_total += 1;
            }
            _ => return false,
        }
        true
    }

    fn decay_plants(&mut self, step: i64) {
        for tile in &mut self.tiles {
            let Tile::Plant(p) = tile else {
                continue;
            };
            let lifespan = p.max_lifespan_step;
            if lifespan < 0 || step < lifespan || (step - lifespan) % 2 != 0 {
                continue;
            }
            p.yield_units -= 1;
            if p.yield_units <= 0 {
                *tile = Tile::Weed;
            }
        }
    }

    fn refresh_plants(&mut self, day: i64, turns_per_day: usize) {
        let next_day = day + 1;
        for tile in &mut self.tiles {
            let Tile::Plant(p) = tile else {
                continue;
            };
            let watered = p.watered_today;
            p.consecutive_unwatered = if watered {
                0
            } else {
                p.consecutive_unwatered + 1
            };
            p.watered_today = false;
            if p.consecutive_unwatered >= 2 {
                *tile = Tile::Weed;
                continue;
            }
            let cd = p.crop.crop();
            if !cd.ongoing {
                continue;
            }
            let since_first = next_day - p.planted_day - cd.first_yield_day;
            if since_first < 0 || since_first % cd.interval != 0 {
                continue;
            }
            let count = since_first / cd.interval + 1;
            if count > i64::from(cd.max_yield) {
                continue;
            }
            let fertilized = watered && p.fertilized_until_day >= day;
            p.yield_units = cd
                .max_yield
                .min(p.yield_units + if fertilized { 2 } else { 1 });
            if count == i64::from(cd.max_yield) {
                p.max_lifespan_step = (next_day + 1) * turns_per_day as i64;
            }
        }
    }

    fn refresh_animals(&mut self, day: i64) {
        for tile in &mut self.tiles {
            let Tile::Animal(a) = tile else {
                continue;
            };
            let ad = a.animal.animal();
            a.consecutive_unfed = if a.fed_today {
                0
            } else {
                a.consecutive_unfed + 1
            };
            if a.consecutive_unfed >= 2 {
                *tile = Tile::Structure(ad.structure);
                continue;
            }
            let since_first = day + 1 - a.placed_day - ad.first_yield_day;
            if since_first >= 0 && since_first % ad.interval == 0 {
                let bonus = if a.fed_today { a.pending_care_bonus } else { 0 };
                a.yield_units = ad.max_held.min(a.yield_units + 1 + bonus);
                // The original also clears a pending bonus on an unfed production day.
                a.pending_care_bonus = 0;
            }
            if a.cared_today && a.fed_today {
                a.pending_care_bonus += 1;
            }
            a.fertilizer_available = true;
            a.fed_today = false;
            a.cared_today = false;
        }
    }

    fn end_day(&mut self, cfg: &Config, day: i64, rng: &mut PythonRandom) {
        self.refresh_plants(day, cfg.turns_per_day);
        self.refresh_animals(day);
        for tile in &mut self.tiles {
            // Draw only on empty tiles, even when chance is zero. Row-major order.
            if matches!(tile, Tile::Empty) && rng.random() < cfg.weed_chance {
                *tile = Tile::Weed;
            }
        }
        for unit in &mut self.units {
            unit.inventory
                .drop_to_shed(&mut self.shed, &mut self.shed_total, cfg.shed_capacity);
        }
        self.units.truncate(1); // Retain the allocation for tomorrow's hires.
        self.units[0].pos = ACCESS[0];
        self.hire_fib = [1, 1];
    }
}

/// One isolated two-seat episode. The ONLY market belongs to the game, not farms.
/// Rayon parallelizes separate Game instances, never seats/turns of one game.
pub struct Game<'a> {
    pub(crate) config: &'a Config,
    pub(crate) seed: i64,
    pub(crate) turn: usize,
    pub(crate) farms: [Farm; 2],
    pub(crate) market_inventory: [f64; PRODUCT_COUNT],
    pub(crate) shops: [u8; SHOP_COUNT],
    pub(crate) shop_len: usize,
    pub(crate) market_loop_aborts: usize,
}

impl<'a> Game<'a> {
    /// Reserve before play; bounds should come from Tape::hand_capacity.
    pub fn new(config: &'a Config, seed: i64, hand_capacities: [usize; 2]) -> Self {
        Self {
            config,
            seed,
            turn: 0,
            farms: std::array::from_fn(|i| Farm::new(config, hand_capacities[i])),
            market_inventory: std::array::from_fn(|i| config.curves[i].i0),
            shops: [0; SHOP_COUNT],
            shop_len: 0,
            market_loop_aborts: 0,
        }
    }

    pub fn turn(&self) -> usize {
        self.turn
    }
    pub fn rewards(&self) -> [f64; 2] {
        [self.farms[0].money, self.farms[1].money]
    }
    pub fn market_loop_aborts(&self) -> usize {
        self.market_loop_aborts
    }

    /// Backward-compatible shorthand applying the same rule to both seats.
    pub fn step(&mut self, actions: [&Action; 2], trim_hands: bool) {
        self.step_with_hand_trimming(actions, [trim_hands; 2]);
    }

    /// Trimming is per physical seat. Raw replay opponents must not inherit
    /// the candidate's wrapper: phantom PLANT requests affect seed validation.
    pub fn step_with_hand_trimming(&mut self, actions: [&Action; 2], trim_hands: [bool; 2]) {
        let day = (self.turn / self.config.turns_per_day) as i64;
        for (seat, farm) in self.farms.iter_mut().enumerate() {
            farm.apply_actions(actions[seat], self.config, day, trim_hands[seat]);
        }
        self.process_market(actions);
        self.town_consume();
        for farm in &mut self.farms {
            farm.decay_plants(self.turn as i64);
        }
        if (self.turn + 1) % self.config.turns_per_day == 0 {
            let mut rng = PythonRandom::for_day(self.seed, day);
            // One shared RNG stream: seat 0 weeds, seat 1 weeds, then shop draw.
            for farm in &mut self.farms {
                farm.end_day(self.config, day, &mut rng);
            }
            if (day + 1) % self.config.shop_unlock_interval as i64 == 0
                && self.shop_len < SHOP_COUNT
            {
                self.shops[self.shop_len] = rng.choice8();
                self.shop_len += 1;
            }
        }
        self.turn += 1;
    }

    fn process_market(&mut self, actions: [&Action; 2]) {
        let count = actions[0]
            .market
            .len()
            .max(actions[1].market.len())
            .min(self.config.max_market_orders);
        for index in 0..count {
            let mut orders: [Order; 2] =
                std::array::from_fn(|i| actions[i].market.get(index).copied().unwrap_or_default());
            for (i, order) in orders.iter_mut().enumerate() {
                match order.kind {
                    OrderKind::Hire => {
                        self.farms[i].hire(self.config);
                        order.kind = OrderKind::Noop;
                    }
                    OrderKind::BuyLand => {
                        self.farms[i].buy_land();
                        order.kind = OrderKind::Noop;
                    }
                    _ => {}
                }
            }
            let mut iterations = 0;
            loop {
                iterations += 1;
                if iterations >= 100_000 {
                    self.market_loop_aborts += 1;
                    break;
                }
                // Quote BOTH against the same inventory BEFORE either commits.
                let quotes: [Option<f64>; 2] = std::array::from_fn(|i| {
                    if orders[i].remaining == 0 {
                        return None;
                    }
                    match orders[i].kind {
                        OrderKind::Sell(item) => Some(
                            self.config.curves[item.index()]
                                .price(self.market_inventory[item.index()]),
                        ),
                        OrderKind::BuyProduct(item) => Some(
                            self.config.curves[item.index()]
                                .price(self.market_inventory[item.index()] - 1.0),
                        ),
                        OrderKind::BuySeed(item) => Some(item.crop().seed),
                        OrderKind::BuyAnimal(item) => Some(item.animal().cost),
                        _ => None,
                    }
                });
                let mut committed_any = false;
                for (i, price) in quotes.into_iter().enumerate() {
                    if let Some(price) = price {
                        if self.farms[i].commit(
                            orders[i].kind,
                            price,
                            &mut self.market_inventory,
                            self.config,
                        ) {
                            orders[i].remaining -= 1;
                            committed_any = true;
                        } else {
                            orders[i].kind = OrderKind::Noop;
                        }
                    }
                }
                if !committed_any {
                    break;
                }
            }
        }
        // No agent reads cached prices in a tape replay. Compute them only for
        // snapshots instead of repeatedly refreshing nine unused dict entries.
    }

    fn town_consume(&mut self) {
        if self.turn % self.config.shop_sell_interval == 0 {
            for &id in &self.shops[..self.shop_len] {
                let products = SHOPS[usize::from(id)].products;
                let multiplier = if products.len() == 1 { 2.0 } else { 1.0 };
                for &item in products {
                    self.market_inventory[item.index()] -= multiplier;
                }
            }
        }
        if self.turn % self.config.center_sell_interval == 0 {
            for inventory in &mut self.market_inventory[..PRODUCT_COUNT - 1] {
                *inventory -= 1.0;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tape::Tape;
    use serde_json::json;

    #[test]
    fn dict_order_survives_deletion_reinsertion_and_overflow() {
        let mut inv = Inventory::default();
        inv.add(Item::Milk, 2);
        inv.add(Item::Wheat, 2);
        assert!(inv.take(Item::Milk, 2));
        inv.add(Item::Milk, 3);
        let mut shed = [0; ITEM_COUNT];
        let mut total = 0;
        inv.drop_to_shed(&mut shed, &mut total, 3);
        assert_eq!(shed[Item::Wheat.index()], 2);
        assert_eq!(shed[Item::Milk.index()], 1);
        assert_eq!(total, 3);
        assert_eq!(inv.len, 0);
        assert_eq!(inv.amounts, [0; ITEM_COUNT]);
    }

    #[test]
    fn shared_market_quotes_are_simultaneous() {
        let cfg = Config::default();
        let tape =
            Tape::from_json(&json!([[{"market": [["BUY_PRODUCT", "WHEAT", 4]]}], [{}]])).unwrap();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.step([tape.action(0, 0), tape.action(0, 0)], false);
        assert_eq!(game.farms[0].money, game.farms[1].money);
        assert_eq!(game.farms[0].shed[0], 4);
        assert_eq!(game.market_inventory[0], 9991.0); // 8 buys + town center at step 0
        let mut expected = 3000.0;
        for inv in [9999.0, 9997.0, 9995.0, 9993.0] {
            expected -= cfg.curves[0].price(inv);
        }
        assert_eq!(game.rewards(), [expected, expected]);
    }

    #[test]
    fn phantom_hands_block_planting_unless_explicitly_trimmed() {
        let cfg = Config::default();
        let tape = Tape::from_json(
            &json!([[{"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]]}], [{}]]),
        )
        .unwrap();
        for trim in [false, true] {
            let mut game = Game::new(&cfg, 0, [0, 0]);
            game.farms[0].seeds[0] = 1;
            game.step([tape.action(0, 0), tape.action(1, 0)], trim);
            assert_eq!(matches!(game.farms[0].tiles[44], Tile::Plant(_)), trim);
        }
    }

    #[test]
    fn floor_sales_do_not_inflate_supply() {
        let cfg = Config::default();
        let mut game = Game::new(&cfg, 0, [0, 0]);
        game.farms[0].shed[Item::Melon.index()] = 1;
        game.farms[0].shed_total = 1;
        game.market_inventory[Item::Melon.index()] = 20000.0;
        assert!(game.farms[0].commit(
            OrderKind::Sell(Item::Melon),
            1.0,
            &mut game.market_inventory,
            &cfg
        ));
        assert_eq!(game.market_inventory[Item::Melon.index()], 20000.0);
    }
}
