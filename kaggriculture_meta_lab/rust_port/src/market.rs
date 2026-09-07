// Rust reimplementation of Kaggriculture 1.32.7 market_price / _shape.
use crate::data::PRODUCT_COUNT;
use serde_json::{json, Value};

#[derive(Clone, Copy, Debug)]
enum Shape {
    Linear,
    Square,
    Sqrt,
    Log,
    Log10,
    Hinge,
}

impl Shape {
    fn parse(name: &str) -> Self {
        match name {
            "sq" => Self::Square,
            "sqrt" => Self::Sqrt,
            "log" => Self::Log,
            "log10" => Self::Log10,
            "hinge" => Self::Hinge,
            _ => Self::Linear, // Python's fallback for unknown function names.
        }
    }
    fn apply(self, x: f64, t: f64) -> f64 {
        let x = x.max(0.0);
        match self {
            Self::Linear => x,
            Self::Square => x * x,
            Self::Sqrt => x.sqrt(),
            Self::Log => (1.0 + x).ln(), // NOT ln_1p: preserve Python's expression.
            Self::Log10 => (1.0 + x).log10(),
            Self::Hinge if t > 0.0 => {
                let u = x / t;
                u + 8.0 * (u - 1.0).max(0.0).powf(2.0)
            }
            Self::Hinge => x,
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct PriceCurve {
    pub base: f64,
    pub i0: f64,
    t: f64,
    below: Shape,
    above: Shape,
    below_amp: f64,
    above_amp: f64,
}

impl PriceCurve {
    pub fn from_json(value: &Value) -> Result<Self, String> {
        fn number(v: &Value, key: &str) -> Result<f64, String> {
            v.get(key)
                .and_then(Value::as_f64)
                .filter(|v| v.is_finite())
                .ok_or_else(|| format!("market parameter {key} must be a finite number"))
        }
        fn shape(v: &Value, key: &str) -> Result<Shape, String> {
            v.get(key)
                .and_then(Value::as_str)
                .map(Shape::parse)
                .ok_or_else(|| format!("market parameter {key} must be a string"))
        }
        let base = number(value, "base")?;
        let i0 = number(value, "I0")?;
        let t = number(value, "T")?;
        let below = shape(value, "below_func")?;
        let above = shape(value, "above_func")?;
        let below_amp = number(value, "below_target")? * base / below.apply(t, t);
        let above_amp = number(value, "above_target")? * base / above.apply(t, t);
        if !below_amp.is_finite() || !above_amp.is_finite() {
            return Err("market T/targets produce an undefined price curve".into());
        }
        Ok(Self {
            base,
            i0,
            t,
            below,
            above,
            below_amp,
            above_amp,
        })
    }

    #[inline]
    pub fn price(&self, inventory: f64) -> f64 {
        let price = if inventory < self.i0 {
            self.base + self.below_amp * self.below.apply(self.i0 - inventory, self.t)
        } else {
            self.base - self.above_amp * self.above.apply(inventory - self.i0, self.t)
        };
        // Python round() uses ties-to-even, unlike Rust round(). Never use FMA.
        price.round_ties_even().max(1.0)
    }
}

pub fn default_params() -> Value {
    let rows: [(f64, f64, &str, f64, &str, f64); PRODUCT_COUNT] = [
        (25.0, 400.0, "sqrt", 0.80, "log", 0.20),
        (35.0, 450.0, "hinge", 1.00, "sqrt", 0.70),
        (60.0, 200.0, "hinge", 0.40, "sqrt", 0.60),
        (120.0, 100.0, "sqrt", 0.70, "linear", 1.60),
        (250.0, 300.0, "log", 0.20, "sq", 3.60),
        (50.0, 332.0, "hinge", 0.40, "log", 0.20),
        (160.0, 122.0, "sqrt", 0.60, "linear", 1.60),
        (200.0, 105.0, "log", 0.20, "sq", 3.20),
        (100.0, 200.0, "linear", 0.40, "linear", 0.40),
    ];
    let mut map = serde_json::Map::new();
    for (i, &(base, t, below, below_target, above, above_target)) in rows.iter().enumerate() {
        map.insert(
            crate::data::ITEM_NAMES[i].into(),
            json!({
                "base": base, "I0": 10000, "T": t,
                "below_func": below, "below_target": below_target,
                "above_func": above, "above_target": above_target,
            }),
        );
    }
    Value::Object(map)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn banker_rounding_and_floor() {
        let curve = PriceCurve::from_json(&json!({
            "base": 10, "I0": 0, "T": 10,
            "below_func": "linear", "below_target": 0.5,
            "above_func": "linear", "above_target": 0.5
        }))
        .unwrap();
        assert_eq!(curve.price(-1.0), 10.0); // 10.5 -> even
        assert_eq!(curve.price(-3.0), 12.0); // 11.5 -> even
        assert_eq!(curve.price(1.0), 10.0); // 9.5 -> even
        assert_eq!(curve.price(3.0), 8.0); // 8.5 -> even
        assert_eq!(curve.price(100.0), 1.0);
    }
}
