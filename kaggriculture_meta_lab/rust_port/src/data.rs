// Rules ported from kaggle-environments 1.32.7 (Apache-2.0).
// This is a Rust reimplementation; the unmodified Python is in reference/.

pub const BOARD_SIZE: usize = 10;
pub const TILE_COUNT: usize = BOARD_SIZE * BOARD_SIZE;
pub const PRODUCT_COUNT: usize = 9;
pub const ITEM_COUNT: usize = 12;
pub const CROP_COUNT: usize = 5;
pub const SHOP_COUNT: usize = 8;
pub const LAND_PRICES: [f64; 3] = [1000.0, 2000.0, 4000.0];
pub const QUADRANTS: [&str; 4] = ["NW", "NE", "SW", "SE"];
pub const ACCESS: [[u8; 2]; 4] = [[4, 4], [5, 4], [4, 5], [5, 5]];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub enum Item {
    Wheat,
    Carrot,
    Tomato,
    Strawberry,
    Melon,
    Egg,
    Milk,
    Wool,
    Fertilizer,
    Goose,
    Cow,
    Sheep,
}

pub const ITEMS: [Item; ITEM_COUNT] = [
    Item::Wheat, Item::Carrot, Item::Tomato, Item::Strawberry, Item::Melon,
    Item::Egg, Item::Milk, Item::Wool, Item::Fertilizer,
    Item::Goose, Item::Cow, Item::Sheep,
];
pub const ITEM_NAMES: [&str; ITEM_COUNT] = [
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL",
    "FERTILIZER", "GOOSE", "COW", "SHEEP",
];

impl Item {
    pub fn parse(s: &str) -> Option<Self> {
        ITEM_NAMES.iter().position(|&name| name == s).map(|i| ITEMS[i])
    }
    pub const fn index(self) -> usize { self as usize }
    pub fn name(self) -> &'static str { ITEM_NAMES[self.index()] }
    pub const fn is_crop(self) -> bool { self.index() < CROP_COUNT }
    pub const fn is_product(self) -> bool { self.index() < PRODUCT_COUNT }
    pub const fn is_animal(self) -> bool { self.index() >= PRODUCT_COUNT }
    pub fn crop(self) -> &'static CropData { &CROPS[self.index()] }
    pub fn animal(self) -> &'static AnimalData { &ANIMALS[self.index() - PRODUCT_COUNT] }
}

pub struct CropData {
    pub seed: f64,
    pub first_yield_day: i64,
    pub max_yield_day: i64,
    pub interval: i64,
    pub max_yield: i32,
    pub ongoing: bool,
}

pub const CROPS: [CropData; CROP_COUNT] = [
    CropData { seed: 10.0, first_yield_day: 2, max_yield_day: 4, interval: 0, max_yield: 6, ongoing: false },
    CropData { seed: 20.0, first_yield_day: 2, max_yield_day: 3, interval: 0, max_yield: 4, ongoing: false },
    CropData { seed: 50.0, first_yield_day: 8, max_yield_day: 8, interval: 1, max_yield: 4, ongoing: true },
    CropData { seed: 100.0, first_yield_day: 10, max_yield_day: 10, interval: 2, max_yield: 4, ongoing: true },
    CropData { seed: 80.0, first_yield_day: 10, max_yield_day: 12, interval: 0, max_yield: 6, ongoing: false },
];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Structure { Coop, Pasture }

impl Structure {
    pub const fn name(self) -> &'static str {
        match self { Self::Coop => "COOP", Self::Pasture => "PASTURE" }
    }
}

pub struct AnimalData {
    pub cost: f64,
    pub structure: Structure,
    pub first_yield_day: i64,
    pub interval: i64,
    pub max_held: i32,
    pub product: Item,
}

pub const ANIMALS: [AnimalData; 3] = [
    AnimalData { cost: 300.0, structure: Structure::Coop, first_yield_day: 4, interval: 1, max_held: 4, product: Item::Egg },
    AnimalData { cost: 400.0, structure: Structure::Pasture, first_yield_day: 8, interval: 2, max_held: 6, product: Item::Milk },
    AnimalData { cost: 500.0, structure: Structure::Pasture, first_yield_day: 6, interval: 3, max_held: 6, product: Item::Wool },
];

pub struct Shop {
    pub name: &'static str,
    pub products: &'static [Item],
}

// Python draws rng.choice(sorted(SHOPS)), NOT insertion order of SHOPS.
pub const SHOPS: [Shop; SHOP_COUNT] = [
    Shop { name: "BAKERY", products: &[Item::Egg, Item::Wheat] },
    Shop { name: "BRUNCH_SPOT", products: &[Item::Egg, Item::Wheat, Item::Strawberry] },
    Shop { name: "FARMERS_MARKET", products: &[Item::Wheat, Item::Carrot, Item::Tomato, Item::Strawberry] },
    Shop { name: "ICE_CREAM_SHOP", products: &[Item::Strawberry, Item::Milk, Item::Wheat] },
    Shop { name: "PET_CAFE", products: &[Item::Carrot] },
    Shop { name: "PIZZA_SHOP", products: &[Item::Milk, Item::Tomato, Item::Wheat] },
    Shop { name: "SMOOTHIE_SHOP", products: &[Item::Strawberry, Item::Milk] },
    Shop { name: "YARN_STORE", products: &[Item::Wool] },
];

pub const fn quadrant(x: usize, y: usize) -> usize {
    (if x >= BOARD_SIZE / 2 { 1 } else { 0 }) + (if y >= BOARD_SIZE / 2 { 2 } else { 0 })
}
