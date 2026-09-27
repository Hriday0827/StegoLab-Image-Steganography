# Phase 2 — Basic LSB Encoding

## What This Phase Does
Hides a text message inside an image using the **Least Significant Bit (LSB)** algorithm. Each bit of the message replaces the last bit of consecutive R, G, B channel bytes. Produces a stego image that looks identical to the original.

## Algorithm
```
Message: "Hi"
H → ASCII 72  → binary 01001000
i → ASCII 105 → binary 01101001
+ delimiter \x00\x01\x00\x01

Bits embedded: 0 1 0 0 1 0 0 0  0 1 1 0 1 0 0 1 ...
Channels used: R G B R G B R G  B R G B R G B R ...
               px0       px1       px2       px3
```

For each channel byte:
- `new_value = (old_value & 0xFE) | message_bit`
- Maximum change per channel: ±1 (invisible to human eye)

## Folder Structure
```
phase2_lsb_encode/
├── lsb_encoder.py      # Core encoding logic + report builder
├── main.py             # CLI runner
├── requirements.txt
├── README.md
└── images/
    ├── input/          # Place cover image here
    └── output/         # stego.png + encoding_report.txt saved here
```

## How to Run
```bash
pip install -r phase2_lsb_encode/requirements.txt

python -m phase2_lsb_encode.main \
  --image phase2_lsb_encode/images/input/sample.png \
  --message "Hello, this is a secret!"

# Custom output filename
python -m phase2_lsb_encode.main \
  --image phase2_lsb_encode/images/input/sample.png \
  --message "Secret" \
  --output my_stego.png
```

## Output
- **`images/output/stego.png`** — stego image (visually identical to original)
- **`images/output/encoding_report.txt`** — full report with:
  1. Encoding summary (capacity, usage, pixels changed)
  2. Text → binary conversion table (every character, ASCII, 8-bit binary)
  3. Original pixel matrix (all pixels with RGB decimal + binary)
  4. Change log (every modified channel: pixel#, row, col, channel, old→new, diff, bit)
  5. Stego pixel matrix (all pixels, modified ones marked with `* CHANGED`)

## Key Concepts
| Concept | Explanation |
|---|---|
| LSB | Bit 0 (rightmost) of each byte — changing it alters value by at most ±1 |
| Delimiter | `\x00\x01\x00\x01` appended to mark end of message for decoder |
| Capacity | W × H × 3 bits total — 3 bits hidden per pixel |
| Distortion | Max ±1 per channel — PSNR typically >50 dB (imperceptible) |

## What Carries Forward
- `encode_lsb()` — Phase 3 decoder reverses this exact process
- Change tracking structure — reused in Phase 4, 5, 6 reports
