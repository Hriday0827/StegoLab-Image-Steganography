# 🔐 StegoLab — Advanced Image Steganography & Steganalysis Suite

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#-testing--verification)

---

## 🎓 Algorithm Design & Complexity

This project explores the design, time and space complexity, and practical implementation of data-hiding algorithms:

1. **Sequential Search & Bitwise Manipulation (Basic LSB)**:
   - **Time Complexity**: $\mathcal{O}(N)$ where $N$ is the number of bits in the message payload.
   - **Space Complexity**: $\mathcal{O}(1)$ auxiliary space for in-place channel bit substitution.
2. **Pseudorandom Permutations (Randomized LSB)**:
   - Utilizes the **Fisher-Yates Shuffle algorithm** $(\mathcal{O}(M)$ time for $M$ channel indices$)$ seeded by a **32-bit `djb2` hash** function $(\mathcal{O}(K)$ for key length $K)$.
   - Eliminates contiguous spatial patterns, defeating sequential Chi-Square steganalysis.
3. **Local Neighborhood & Spatial Masking (Edge-Adaptive)**:
   - Uses a **$3 \times 3$ Sliding Window Variance Filter** $(\mathcal{O}(W \times H)$ time$)$ to dynamically scale embedding bit depth $(1 \text{ to } 3 \text{ bits})$ based on local spatial frequencies and Human Visual System (HVS) masking.

---

## 🌟 Key Features

- **3 Active Algorithmic Paradigms**:
  1. **Basic LSB (Sequential)**: Deterministic 1-bit spatial LSB substitution across RGB channels.
  2. **Randomized LSB (Key-Secured)**: Key-seeded Fisher-Yates channel shuffling using `djb2` hash algorithms to defeat sequential analysis.
  3. **Edge-Adaptive (Local Variance)**: 3×3 luminance variance estimation allocating 1 to 3 bits in high-frequency/textured regions while preserving smooth areas.
- **Interactive Visual Cyber-Lab**:
  - Live Drag & Drop carrier image preview with instant dimension & pixel metadata.
  - Real-time **Capacity Gauge** calculating payload limits and utilization percentages.
  - Step-by-step **Process Execution Log**.
  - **Text → Binary Bitstream Breakdown** (ASCII, Unicode & Emojis supported).
  - **RGB Pixel Matrix Inspector** comparing original vs. stego values side-by-side with changed bits highlighted.
  - **Bit-Level Change & Extraction Log** tracking modified channel registers.
  - **Lossless PNG Export** ensuring bit-perfect stego preservation.
  - One-click copy for extracted payloads.
- **Cross-Platform Compatibility**: Full UTF-8 support for Windows (PowerShell/CMD), Linux, and macOS without encoding crashes.
- **Automated Test Suite**: Built-in self-testing framework verifying all encoding/decoding cycles with 100% data integrity.

---

## 📂 Project Architecture

```
stegolab/
├── shared/                       # Reusable core modules (imported by all phases)
│   ├── image_io.py               # Lossless PIL <-> NumPy loaders and dimension helpers
│   ├── binary_utils.py           # UTF-8 text <-> bitstream conversions & delimiters
│   └── report_utils.py           # Formatted report utilities & console layout
│
├── phase1_basics/                # Phase 1: Pixel matrix extraction & RGB statistics
├── phase2_lsb_encode/            # Phase 2: Sequential LSB encoding engine
├── phase3_lsb_decode/            # Phase 3: Sequential LSB decoding engine
├── phase4_random_lsb/            # Phase 4: Randomized key-seeded LSB (Encode + Decode)
├── phase5_edge_adapt/            # Phase 5: Edge-Adaptive variance-based steganography
│
├── phase5_webapp/                # Interactive Flask Web Studio
│   ├── app.py                    # REST API endpoints & server
│   ├── algorithms/               # Clean dispatch interface
│   ├── static/                   # Minimalist CSS design system & dynamic JavaScript
│   └── templates/                # Responsive HTML5 studio
│
├── tests/                        # Automated unit & integration tests
│   └── test_api.py               # End-to-end Flask test client suite
│
├── run.py                        # Unified root runner (Web studio & automated tests)
├── requirements.txt              # Project dependencies
├── CONCEPTS.md                   # In-depth algorithmic & theoretical reference
└── README.md                     # Documentation
```

---

## 🚀 Quick Start Guide

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/stegolab.git
cd stegolab
```

### Step 2: Set Up Environment & Install Dependencies

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Step 3: Launch the Interactive Web Studio

Start the web studio with the root runner:
```bash
python run.py
```
Open your browser and navigate to **`http://127.0.0.1:5000`**.

> **Tip:** You can specify a custom port with `python run.py --port 8080`.

---

## 🧪 Testing & Verification

Run the built-in automated test suite to verify all algorithms and end-to-end API endpoints:

```bash
# Run multi-algorithm verification test
python run.py --test

# Run full unittest suite
python -m unittest discover tests
```

---

## 💻 CLI Usage (Phase-by-Phase)

You can run each phase individually from the project root:

### 1. Image Pixel Analysis (Phase 1)
```bash
python -m phase1_basics.main --image phase1_basics/images/input/sample.png --pixels 20
```

### 2. Basic LSB (Phases 2 & 3)
```bash
# Encode
python -m phase2_lsb_encode.main --image phase2_lsb_encode/images/input/sample.png --message "Hello World"

# Decode
python -m phase3_lsb_decode.main --image phase2_lsb_encode/images/output/stego.png
```

### 3. Randomized LSB (Phase 4)
```bash
# Encode with key
python -m phase4_random_lsb.main --mode encode --image phase4_random_lsb/images/input/sample.png --message "Classified" --key "mySecretKey"

# Decode with matching key
python -m phase4_random_lsb.main --mode decode --image phase4_random_lsb/images/output/stego_random.png --key "mySecretKey"
```

### 4. Edge-Adaptive Steganography (Phase 5)
```bash
# Encode
python -m phase5_edge_adapt.main --mode encode --image phase5_edge_adapt/images/input/sample.png --message "Adaptive Text"

# Decode
python -m phase5_edge_adapt.main --mode decode --image phase5_edge_adapt/images/output/stego_edge.png
```

---

## 📊 Algorithm Comparison & Complexity

| Algorithm | Traversal Strategy | Bit Depth Allocation | Time Complexity | Chi-Square Resistance |
|---|---|---|---|---|
| **Basic LSB** | Sequential (Row-Major) | Fixed 1-bit | $\mathcal{O}(N)$ | Low (Sequential pattern detectable) |
| **Randomized LSB** | Fisher-Yates Permutation | Fixed 1-bit | $\mathcal{O}(M + K)$ | High (Scatters bits across channels) |
| **Edge-Adaptive** | Sequential (Row-Major) | Dynamic (1–3 bits via 3×3 Variance) | $\mathcal{O}(W \cdot H)$ | High (Masked in high-frequency regions) |

---

## 📜 Quality & Imperceptibility Metrics

- **Peak Signal-to-Noise Ratio (PSNR)**:
  $$\text{PSNR} = 10 \cdot \log_{10}\left(\frac{255^2}{\text{MSE}}\right)$$
  - StegoLab algorithms consistently achieve **PSNR > 50 dB** (imperceptible to human vision).
- **Format Guarantee**: All stego images are saved losslessly as **PNG** to prevent discrete cosine transform (DCT) artifacts from corrupting embedded LSB bits.

---

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
