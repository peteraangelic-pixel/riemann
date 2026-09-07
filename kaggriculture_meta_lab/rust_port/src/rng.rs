//! CPython's integer-seeded MT19937, random() and getrandbits-based choice.
//! Do not replace this with StdRng, a numpy generator, or a modulo draw.
//! Integer seeds are split into little-endian 32-bit words of abs(seed).

const N: usize = 624;

pub struct PythonRandom {
    state: [u32; N],
    index: usize,
}

impl PythonRandom {
    pub fn new(seed: i128) -> Self {
        let value = seed.unsigned_abs();
        let mut key = [0_u32; 4];
        let len = ((128 - value.leading_zeros()) as usize).div_ceil(32).max(1);
        for (i, word) in key.iter_mut().enumerate().take(len) {
            *word = (value >> (32 * i)) as u32;
        }
        let mut rng = Self { state: [0; N], index: N };
        rng.state[0] = 19_650_218;
        for i in 1..N {
            let prev = rng.state[i - 1];
            rng.state[i] = 1_812_433_253_u32.wrapping_mul(prev ^ (prev >> 30)).wrapping_add(i as u32);
        }
        let (mut i, mut j) = (1, 0);
        for _ in 0..N.max(len) {
            let prev = rng.state[i - 1];
            rng.state[i] = (rng.state[i] ^ (prev ^ (prev >> 30)).wrapping_mul(1_664_525))
                .wrapping_add(key[j]).wrapping_add(j as u32);
            i += 1;
            j += 1;
            if i >= N { rng.state[0] = rng.state[N - 1]; i = 1; }
            if j >= len { j = 0; }
        }
        for _ in 0..N - 1 {
            let prev = rng.state[i - 1];
            rng.state[i] = (rng.state[i] ^ (prev ^ (prev >> 30)).wrapping_mul(1_566_083_941))
                .wrapping_sub(i as u32);
            i += 1;
            if i >= N { rng.state[0] = rng.state[N - 1]; i = 1; }
        }
        rng.state[0] = 0x8000_0000;
        rng
    }

    pub fn for_day(seed: i64, day: i64) -> Self {
        // i128 is essential: CPython multiplication does not wrap at 32/64 bits.
        Self::new((i128::from(seed) * 1_000_003) ^ i128::from(day))
    }

    fn twist(&mut self) {
        for i in 0..N {
            let y = (self.state[i] & 0x8000_0000) | (self.state[(i + 1) % N] & 0x7fff_ffff);
            self.state[i] = self.state[(i + 397) % N] ^ (y >> 1) ^ (if y & 1 != 0 { 0x9908_b0df } else { 0 });
        }
        self.index = 0;
    }

    pub fn next_u32(&mut self) -> u32 {
        if self.index == N { self.twist(); }
        let mut y = self.state[self.index];
        self.index += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c_5680;
        y ^= (y << 15) & 0xefc6_0000;
        y ^= y >> 18;
        y
    }

    pub fn random(&mut self) -> f64 {
        let a = u64::from(self.next_u32() >> 5);
        let b = u64::from(self.next_u32() >> 6);
        ((a << 26) + b) as f64 * (1.0 / 9_007_199_254_740_992.0)
    }

    pub fn choice8(&mut self) -> u8 {
        // _randbelow(8) uses 8.bit_length() == 4, including rejection draws.
        loop {
            let value = self.next_u32() >> 28;
            if value < 8 { return value as u8; }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cpython_seed_zero() {
        let mut rng = PythonRandom::new(0);
        for expected in [0.8444218515250481_f64, 0.7579544029403025, 0.420571580830845, 0.25891675029296335, 0.5112747213686085] {
            assert_eq!(rng.random().to_bits(), expected.to_bits());
        }
        let mut rng = PythonRandom::new(0);
        assert_eq!((0..10).map(|_| rng.choice8()).collect::<Vec<_>>(), [6, 6, 0, 4, 7, 6, 4, 7, 5, 3]);
    }

    #[test]
    fn negative_integer_seeds_use_magnitude() {
        let mut a = PythonRandom::new(-12_345_678_901_234_567_890);
        let mut b = PythonRandom::new(12_345_678_901_234_567_890);
        for _ in 0..2000 { assert_eq!(a.next_u32(), b.next_u32()); }
    }
}
