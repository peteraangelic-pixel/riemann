//! Count allocator calls on the replay thread, not test-harness/Rayon startup.
use kg_sim::{Config, PreparedTape, Replay, Tape};
use serde_json::json;
use std::{
    alloc::{GlobalAlloc, Layout, System},
    cell::Cell,
};

struct CountingAllocator;
thread_local! {
    static TRACK: Cell<bool> = const { Cell::new(false) };
    static COUNT: Cell<usize> = const { Cell::new(0) };
}
fn note() {
    if TRACK.try_with(Cell::get).unwrap_or(false) {
        let _ = COUNT.try_with(|c| c.set(c.get() + 1));
    }
}
unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        note();
        unsafe { System.alloc(layout) }
    }
    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        note();
        unsafe { System.alloc_zeroed(layout) }
    }
    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        note();
        unsafe { System.realloc(ptr, layout, new_size) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
}
#[global_allocator]
static ALLOCATOR: CountingAllocator = CountingAllocator;

#[test]
fn no_heap_allocations_including_free_hires_and_daily_refresh() {
    let cfg = Config::from_json(
        &json!({"farmHandCostMult": 0, "startingMoney": 100000, "shedCapacity": 3}),
    )
    .unwrap();
    let mut actions = vec![
        json!({"market": [["BUY_LAND"], ["BUY_LAND"], ["BUY_LAND"], ["BUY_SEED", "TOMATO", 5], ["BUY_ANIMAL", "COW", 1]]}),
    ];
    for op in [
        json!(["PICKUP", "COW"]),
        json!(["BUILD_PASTURE"]),
        json!(["PLACE", "COW"]),
        json!(["CARE"]),
        json!(["NORTH"]),
        json!(["PLANT", "TOMATO"]),
        json!(["WATER"]),
        json!(["HARVEST"]),
        json!(["DROP"]),
    ] {
        actions.push(json!({"farmer": op, "market": [["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1], ["SELL", "WHEAT", 1]]}));
    }
    // Last entry repeats: 48 free hires each full day, capacity reused on reset.
    let tape = PreparedTape::new(Tape::from_json(&json!([actions, [{}]])).unwrap(), &cfg, 720);
    let mut replay = Replay::new(&cfg, &tape, &tape, -71, false, false);
    COUNT.with(|c| c.set(0));
    TRACK.with(|c| c.set(true));
    while replay.advance() {}
    TRACK.with(|c| c.set(false));
    assert_eq!(COUNT.with(Cell::get), 0);
    assert_eq!(replay.game.turn(), 720);
    assert!(replay.outcome().errors.is_empty());
}
