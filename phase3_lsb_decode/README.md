# Phase 3 — LSB Decoding

## What This Phase Does
Extracts the hidden message from a stego image produced by Phase 2. Reads the LSB of each channel byte in the same sequential order used during encoding, reconstructs bits into characters, and stops at the delimiter.

## Algorithm
```
Stego pixel channel bytes (R, G, B per pixel):
  pixel 0: R=200 (11001000) → LSB=0
           G=101 (01100101) → LSB=1
           B=72  (01001000) → LSB=0  ...

Collected bits: 0 1 0 0 1 0 0 0 → byte = 72 → 'H'
Next 8 bits   : 0 1 1 0 1 0 0 1 → byte = 105 → 'i'
...until \x00\x01\x00\x01 delimiter found → stop
```

## Folder Structure
```
phase3_lsb_decode/
├── lsb_decoder.py      # Core decoding logic + report builder
├── main.py             # CLI runner
├── requirements.txt
├── README.md
└── images/
    ├── input/          # Place stego image here (output from Phase 2)
    └── output/         # decoding_report.txt saved here
```

## How to Run
```bash
pip install -r phase3_lsb_decode/requirements.txt

# Decode a stego image
python -m phase3_lsb_decode.main \
  --image phase3_lsb_decode/images/input/stego.png
```

## Typical Workflow
```bash
# Step 1 — Encode (Phase 2)
python -m phase2_lsb_encode.main \
  --image phase2_lsb_encode/images/input/sample.png \
  --message "Hello World"

# Step 2 — Copy stego image to Phase 3 input
cp phase2_lsb_encode/images/output/stego.png \
   phase3_lsb_decode/images/input/stego.png

# Step 3 — Decode (Phase 3)
python -m phase3_lsb_decode.main \
  --image phase3_lsb_decode/images/input/stego.png
```

## Output
- **Terminal** — decoded message printed immediately
- **`images/output/decoding_report.txt`** — full report with:
  1. Decoding summary (bits read, message length, delimiter found)
  2. Bit extraction log (every channel byte: value, binary, LSB extracted)
  3. Bits → text reconstruction table (every 8 bits → character)
  4. Image integrity statistics (channel min/max/mean/std)

## Key Concepts
| Concept | Explanation |
|---|---|
| LSB read | `lsb = byte_value & 1` — isolate rightmost bit |
| Bit assembly | 8 LSBs collected → shifted into byte → ASCII character |
| Delimiter | Stop condition: `\x00\x01\x00\x01` found in decoded stream |
| Integrity | Channel statistics confirm minimal distortion from encoding |

## What Carries Forward
- `decode_lsb()` — Phase 4 randomized decoder mirrors this with shuffled positions
- `compute_integrity()` — used in Phases 4, 5, 6 for quality verification
