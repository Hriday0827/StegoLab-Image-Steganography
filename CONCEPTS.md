# StegoLab — Concepts & Algorithm Documentation

A comprehensive reference for all algorithms, design decisions, and theoretical foundations implemented across Phases 1–7.

---

## Table of Contents
1. What is Steganography?
2. Why Images?
3. Image Fundamentals
4. Algorithm 1 — Basic LSB
5. Algorithm 2 — Randomized LSB
6. Algorithm 3 — Edge-Adaptive
7. Algorithm 4 — Hybrid
8. Image Quality Metrics
9. Security Analysis
10. Design Decisions
11. Phase Dependency Map

---

## 1. What is Steganography?

Steganography is the practice of hiding secret information within an ordinary carrier file so that the existence of the hidden data is not detectable. Unlike encryption (which makes data unreadable but visible), steganography makes data invisible — the carrier looks completely normal.

    Encryption:    "Hello" → "Xk92@#mP"          ← obviously encrypted
    Steganography: "Hello" → [normal-looking image] ← secret is invisible

Key terminology:
  - Cover image    : Original unmodified image used as carrier
  - Stego image    : Image after the message has been hidden
  - Payload        : The hidden secret message
  - Capacity       : Maximum number of bits that can be hidden
  - Imperceptibility: How undetectable the changes are to the human eye
  - Steganalysis   : The science of detecting hidden steganography

---

## 2. Why Images?

Digital images are ideal steganography carriers because:
  - Redundancy: a 512x512 image has 786,432 channel bytes; changing a fraction is imperceptible
  - Perceptual insensitivity: humans cannot detect a ±1 change in a pixel channel value
  - Lossless formats: PNG and BMP preserve every bit exactly across save/load cycles
  - Ubiquity: images are shared constantly, hiding suspicious communication patterns

Why PNG for output?
  JPEG compression is lossy — it destroys LSB data on every save. All stego output
  is PNG to guarantee bit-perfect preservation.

---

## 3. Image Fundamentals

### Pixel representation
A digital image is a 2D grid of pixels. Each pixel stores three 8-bit integers: R, G, B.

    Pixel (row=0, col=0): R=200, G=150, B=72
    Binary:               R=11001000, G=10010110, B=01001000

### NumPy array shape
    array.shape = (H, W, 3)     H=height, W=width, 3=channels
    array[row, col, 0]          Red
    array[row, col, 1]          Green
    array[row, col, 2]          Blue

### The Least Significant Bit (LSB)
The LSB is the rightmost bit (position 0). Changing it alters the value by at most ±1.

    Original R = 200 = 11001000    LSB = 0
    Embed bit 1:
    New R      = 201 = 11001001    LSB = 1    change = +1, imperceptible

---

## 4. Algorithm 1 — Basic LSB  (Phase 2 + 3)

### Concept
Replace the LSB of each channel byte sequentially with one bit of the message.
Order: R of pixel 0 → G of pixel 0 → B of pixel 0 → R of pixel 1 → ...

### Encoding
    1. Append delimiter:   message + "\x00\x01\x00\x01"
    2. Convert to bits:    each char → 8 bits, MSB first
    3. For each bit:       channel = (channel & 0xFE) | message_bit
    4. Save stego as PNG

### Decoding
    1. Read LSB of each channel byte in same order
    2. Collect 8 bits → reconstruct one character
    3. Stop when delimiter "\x00\x01\x00\x01" is found

### Properties
    Capacity:              W x H x 3 bits
    Max change/channel:    ±1
    Bit depth:             1 bit per channel
    Key required:          No
    Detection risk:        HIGH — Chi-square test reveals sequential pattern

---

## 5. Algorithm 2 — Randomized LSB  (Phase 4)

### Concept
Same 1-bit embedding as Basic LSB, but channel positions are shuffled using
a key-derived seed. Without the key, the position order is unknowable.

### Key → Seed → Shuffle
    Step 1: djb2 hash
            h = 5381
            for each char c: h = ((h << 5) + h + ord(c)) & 0xFFFFFFFF

    Step 2: Fisher-Yates shuffle (LCG RNG)
            state = hash_value
            for i from n-1 down to 1:
                state = (1664525 * state + 1013904223) & 0xFFFFFFFF
                j     = state % (i + 1)
                swap(indices[i], indices[j])

    Step 3: Embed bit[k] at shuffled channel position k

### Properties
    Capacity:              W x H x 3 bits (same as LSB)
    Max change/channel:    ±1
    Key required:          YES
    Detection risk:        MEDIUM — positional analysis fails

---

## 6. Algorithm 3 — Edge-Adaptive  (Phase 5)

### Concept
Embed more bits in edge/textured regions (where the human eye is least sensitive),
fewer bits in smooth regions.

### Local variance
    Luminance: L = 0.299R + 0.587G + 0.114B   (ITU-R BT.601)
    For pixel (r,c): collect L of all 9 neighbours in 3x3 window
    mean  = sum(L) / count
    var   = sum((L - mean)^2) / count

### Variance → bit depth
    var < 200        depth = 1  (smooth)
    200 <= var < 800 depth = 2  (mid-texture)
    var >= 800       depth = 3  (edge/noisy)

### Multi-bit embedding
    mask    = ~((1 << depth) - 1) & 0xFF
    new_val = (old_val & mask) | fragment
    Max change: depth=1 → ±1,  depth=2 → ±3,  depth=3 → ±7

### Properties
    Capacity:              Variable (2-3x more than LSB in textured images)
    Key required:          No (variance map recomputed from image)
    Detection risk:        MEDIUM — variance-aware, harder to detect

---

## 7. Algorithm 4 — Hybrid  (Phase 6)

Three independent techniques combined in one encoding pass.

### Layer 1 — Spiral Traversal
Pixels visited inward-spiral: top-row → right-col → bottom-row → left-col → inward.
Defeats sequential positional analysis.

### Layer 2 — Adaptive Bit Depth
Same as Phase 5: variance → 1, 2, or 3 bits per channel.
Defeats uniform bit-depth analysis.

### Layer 3 — Key-Driven Channel Rotation
    ch_offset = (key_hash >> (step % 16)) & 0x3
    channel   = (step + ch_offset) % 3     (0=R, 1=G, 2=B)
Defeats fixed-channel pattern analysis.

### Properties
    Capacity:              Same as edge-adaptive
    Key required:          YES
    Detection risk:        LOW — 3 independent layers of obfuscation

---

## 8. Image Quality Metrics

### PSNR (Peak Signal-to-Noise Ratio)
    MSE  = mean((original - stego)^2)  over all pixels and channels
    PSNR = 10 * log10(255^2 / MSE)    in dB
    > 40 dB = imperceptible.  LSB typically achieves 50-55 dB.

### Per-algorithm quality
    Algorithm              Max change/ch    Typical PSNR
    Basic LSB              ±1               ~51 dB
    Randomized LSB         ±1               ~51 dB
    Edge-Adaptive (d=2)    ±3               ~45 dB
    Edge-Adaptive (d=3)    ±7               ~40 dB
    Hybrid                 depth-dependent  ~43 dB

---

## 9. Security Analysis

    Attack                 LSB      Random LSB   Edge-Adapt   Hybrid
    Chi-square test        FAIL     PASS         PASS         PASS
    Sequential analysis    FAIL     PASS         PASS         PASS
    LSB plane analysis     FAIL     PARTIAL      PASS         PASS
    Without key            N/A      Cannot dec.  N/A          Cannot dec.

Chi-square test: Basic LSB makes the histogram of LSB values artificially uniform.
Randomized and edge-adaptive algorithms break this statistical regularity.

---

## 10. Design Decisions

### Delimiter: \x00\x01\x00\x01
  - 4 bytes appended before embedding; decoder stops when found
  - No need to store message length separately
  - Rare in natural text; reliable stop signal

### PNG output only
  - JPEG is lossy and destroys LSB data
  - All stego images forced to PNG regardless of input format

### MSB-first bit order
  - Most significant bit embedded first (standard for ASCII)
  - Consistent across all 4 algorithms

### Shared utilities (shared/)
  - image_io.py, binary_utils.py, report_utils.py
  - Zero code duplication — every phase imports, never copies

### Flask over Django for Phase 7
  - Thin wrapper — algorithms plug in directly
  - No ORM, no admin overhead
  - Entire backend is one file (~200 lines)
  - Simple to run locally: python app.py

---

## 11. Phase Dependency Map

    shared/
      image_io.py          ← ALL phases
      binary_utils.py      ← ALL phases
      report_utils.py      ← ALL phases

    phase1_basics/pixel_matrix.py
      extract_pixel_matrix()   → phase2
      get_pixel_data()         → phase2,4,5,6

    phase2_lsb_encode/lsb_encoder.py
      encode_lsb()             → phase7

    phase3_lsb_decode/lsb_decoder.py
      decode_lsb()             → phase7
      compute_integrity()      → phase4,5,6

    phase4_random_lsb/random_lsb.py
      djb2_hash()              → phase6, phase7
      fisher_yates_shuffle()   → phase6
      encode_random_lsb()      → phase7
      decode_random_lsb()      → phase7

    phase5_edge_adapt/edge_adaptive.py
      local_variance()         → phase6, phase7
      bits_for_variance()      → phase6, phase7
      encode_edge_adaptive()   → phase7
      decode_edge_adaptive()   → phase7

    phase6_hybrid/hybrid.py
      spiral_order()           → phase7
      channel_at()             → phase7
      encode_hybrid()          → phase7
      decode_hybrid()          → phase7

    phase7_webapp/
      algorithms/__init__.py   ← imports everything above
      app.py                   ← Flask routes
      templates/index.html     ← UI
      static/style.css + app.js
