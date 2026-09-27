# Phase 7 — Flask Web Application

## What This Phase Does
Exposes all four steganography algorithms (Phases 2–6) through a modern, research-oriented web interface. Upload an image, enter a message, select an algorithm, encode or decode — all results displayed interactively in the browser.

## Folder Structure
```
phase7_webapp/
├── app.py                  # Flask backend — all API routes
├── requirements.txt
├── README.md
├── algorithms/
│   └── __init__.py         # Central import for all algorithm modules
├── templates/
│   └── index.html          # Single-page web UI
├── static/
│   ├── style.css           # Paper/ink research-style stylesheet
│   └── app.js              # Frontend logic (fetch, render, tabs)
└── images/
    ├── uploads/            # Uploaded images saved here (auto-created)
    └── results/            # Encoded stego images saved here
```

## How to Run
```bash
# From project root
pip install -r phase7_webapp/requirements.txt

cd phase7_webapp
python app.py

# Open browser at:
http://localhost:5000
```

## API Endpoints
| Route | Method | Description |
|---|---|---|
| `GET /` | GET | Serve web UI |
| `/api/encode` | POST | Encode message into image |
| `/api/decode` | POST | Decode message from stego image |
| `/api/download/<id>` | GET | Download stego image |

### Encode form fields
| Field | Type | Description |
|---|---|---|
| `image` | file | Cover image (PNG/JPG/BMP) |
| `message` | text | Secret message |
| `algo` | text | `lsb` / `rlsb` / `edge` / `hybrid` |
| `key` | text | Secret key (rlsb and hybrid only) |

## UI Features
- **Algorithm tabs** — switch between 4 algorithms
- **Encode / Decode** mode toggle
- **Capacity bar** — live message length vs image capacity
- **Process log** — step-by-step encoding/decoding summary
- **Text → Binary** tab — every character shown with ASCII + 8-bit binary + individual bit cells
- **Pixel Matrix** tab — full scrollable table of all pixels (original + stego, changed rows highlighted)
- **Bit Changes** tab — every modified channel byte with old/new binary, diff, bit embedded
- **Output** tab — stego image preview or decoded message display
- **Download button** — save stego image

## Notes
- Images are saved to `images/uploads/` and `images/results/` with random UUID filenames
- PNG format used for all stego output (lossless — required for LSB integrity)
- Key field only visible/relevant for Random LSB and Hybrid algorithms
