# Phase 1 — Image Processing Basics

## What This Phase Does
Loads an image, converts it to a pixel matrix, extracts RGB values in decimal and binary, and generates a structured report.

## Folder Structure
```
phase1_basics/
├── pixel_matrix.py     # Core logic — extraction + report
├── main.py             # CLI runner
├── requirements.txt
├── README.md
└── images/
    ├── input/          # Place your test image here
    └── output/         # pixel_report.txt saved here
```

## How to Run
```bash
# From project root
pip install -r phase1_basics/requirements.txt

# Default (10 pixels)
python -m phase1_basics.main --image phase1_basics/images/input/sample.png

# Custom count
python -m phase1_basics.main --image phase1_basics/images/input/sample.png --pixels 25
```

## Output
- **Terminal** — full structured report
- **`images/output/pixel_report.txt`** — saved report with:
  - Image metadata (dimensions, total pixels, capacity, bit depth)
  - Pixel table: index, row, col, R/G/B decimal + 8-bit binary
  - Matrix statistics (min, max, mean, std per channel)

## Key Concepts
| Concept | Explanation |
|---|---|
| Pixel matrix | (H, W, 3) NumPy array — rows × columns × RGB channels |
| 8-bit channel | Each R/G/B value is 0–255 stored as unsigned 8-bit integer |
| Binary repr | Each channel shown as 8 binary digits, e.g. `10110011` |
| LSB | Least Significant Bit — rightmost bit, changed in Phase 2 |
| Capacity | W × H × 3 bits available for 1-bit LSB steganography |

## What Carries Forward
- `shared/image_io.py` — used by all phases
- `extract_pixel_matrix()` — Phase 2 reads pixel matrix for encoding
- `get_pixel_data()` — Phase 2 builds change report on top of this
