# Phase 4 — Randomized LSB

## What This Phase Does
Extends Phase 2 (Basic LSB) by randomizing the order in which channel bytes are used. A secret key is hashed to produce a seed, which shuffles all channel indices. Bits are embedded at the shuffled positions — making sequential analysis impossible without the key.

## Algorithm
```
Key "mykey123"
  → djb2 hash = 2459179873  (seed)
  → Fisher-Yates shuffle of [0, 1, 2, ..., W×H×3-1]
  → shuffle = [4821, 302, 11043, 78, ...]

Bit 0 embedded at channel 4821  →  pixel 1607, channel R
Bit 1 embedded at channel  302  →  pixel  100, channel G
Bit 2 embedded at channel 11043 →  pixel 3681, channel B
...
```

## How to Run
```bash
pip install -r phase4_random_lsb/requirements.txt

# Encode
python -m phase4_random_lsb.main --mode encode \
  --image phase4_random_lsb/images/input/sample.png \
  --message "Hello Secret" --key "mykey123"

# Decode (must use same key)
python -m phase4_random_lsb.main --mode decode \
  --image phase4_random_lsb/images/output/stego_random.png \
  --key "mykey123"
```

## Output Files
| File | Description |
|---|---|
| `images/output/stego_random.png` | Stego image |
| `images/output/encoding_report.txt` | Full encoding report |
| `images/output/decoding_report.txt` | Full decoding report |

## Report Sections (Encoding)
1. Encoding summary (key, hash, seed, usage)
2. Key → hash → shuffle walkthrough (char by char)
3. Text → binary conversion table
4. Original pixel matrix (all pixels)
5. Change log (bit index, shuffle position, pixel, channel, old/new/diff)
6. Stego pixel matrix (all pixels, `* CHANGED` marked)

## Key Concepts
| Concept | Explanation |
|---|---|
| djb2 hash | Deterministic string → integer hash |
| Fisher-Yates | Unbiased in-place shuffle using LCG RNG |
| LCG | Linear Congruential Generator: `s = (1664525*s + 1013904223) mod 2^32` |
| Security | Without key, attacker cannot reconstruct shuffle order |

## What Carries Forward
- `djb2_hash()` — reused in Phase 6 hybrid channel rotation
- `fisher_yates_shuffle()` — reused in Phase 6
