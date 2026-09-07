//! Optional, allocation-heavy diagnostics. Never called by the fast replay loop.
use serde_json::{json, Map, Value};
use crate::{data::*, engine::{Animal, Farm, Game, Inventory, Plant, Tile}};

fn inventory_json(inv: &Inventory) -> Value {
    let map: Map<String, Value> = inv.order[..inv.len].iter()
        .map(|&item| (item.name().into(), json!(inv.amounts[item.index()])))
        .collect();
    Value::Object(map)
}

fn plant_json(p: &Plant) -> Value {
    json!({
        "kind": "PLANT", "crop": p.crop.name(), "planted_day": p.planted_day,
        "watered_today": p.watered_today, "consecutive_unwatered": p.consecutive_unwatered,
        "yield_units": p.yield_units, "max_lifespan_step": p.max_lifespan_step,
        "fertilized_until_day": p.fertilized_until_day,
    })
}

fn animal_json(a: &Animal) -> Value {
    json!({
        "kind": a.animal.animal().structure.name(), "animal": a.animal.name(),
        "placed_day": a.placed_day, "yield_units": a.yield_units,
        "consecutive_unfed": a.consecutive_unfed, "fed_today": a.fed_today,
        "cared_today": a.cared_today, "fertilizer_available": a.fertilizer_available,
        "pending_care_bonus": a.pending_care_bonus,
    })
}

fn tile_json(tile: &Tile) -> Value {
    match tile {
        Tile::Empty => Value::Null,
        Tile::Locked => json!("LOCKED"),
        Tile::Weed => json!({"kind": "WEED"}),
        Tile::Structure(s) => json!({"kind": s.name()}),
        Tile::Plant(p) => plant_json(p),
        Tile::Animal(a) => animal_json(a),
    }
}

fn farm_json(farm: &Farm) -> Value {
    json!({
        "money": farm.money,
        "tiles": farm.tiles.chunks_exact(BOARD_SIZE).map(|row| row.iter().map(tile_json).collect::<Vec<_>>()).collect::<Vec<_>>(),
        "farmer": farm.units[0].pos,
        "hands": farm.units[1..].iter().map(|u| u.pos).collect::<Vec<_>>(),
        "unlocked_quadrants": QUADRANTS[..farm.unlocked],
        "hires_today": farm.units.len() - 1,
    })
}

fn private_json(farm: &Farm) -> Value {
    let shed: Map<String, Value> = ITEMS.iter().map(|item| (item.name().into(), json!(farm.shed[item.index()]))).collect();
    let seeds: Map<String, Value> = ITEMS[..CROP_COUNT].iter().map(|item| (item.name().into(), json!(farm.seeds[item.index()]))).collect();
    json!({
        "shed": shed, "seeds": seeds,
        "inventories": farm.units.iter().map(|u| inventory_json(&u.inventory)).collect::<Vec<_>>(),
    })
}

impl Game<'_> {
    /// Full mechanics state, in physical seat order, initial state included at turn 0.
    /// Framework-only observation fields (timeouts/status/replay log) are excluded.
    pub fn snapshot(&self) -> Value {
        let inventory: Map<String, Value> = ITEMS[..PRODUCT_COUNT].iter()
            .map(|item| (item.name().into(), json!(self.market_inventory[item.index()]))).collect();
        let prices: Map<String, Value> = ITEMS[..PRODUCT_COUNT].iter().map(|item| {
            let i = item.index();
            let price = if self.turn == 0 { self.config.curves[i].base } else { self.config.curves[i].price(self.market_inventory[i]) };
            (item.name().into(), json!(price))
        }).collect();
        let mut market = json!({"inventory": inventory, "prices": prices});
        if let Some(params) = &self.config.resolved_params { market["params"] = params.clone(); }
        json!({
            "step": self.turn,
            "day": self.turn / self.config.turns_per_day,
            "hour": self.turn % self.config.turns_per_day,
            "farms": self.farms.iter().map(farm_json).collect::<Vec<_>>(),
            "privates": self.farms.iter().map(private_json).collect::<Vec<_>>(),
            "market": market,
            "town": {"unlocked_shops": self.shops[..self.shop_len].iter().map(|&i| SHOPS[usize::from(i)].name).collect::<Vec<_>>()},
        })
    }
}
