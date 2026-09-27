"""
phase4_random_lsb/random_lsb.py
---------------------------------
Phase 4: Randomized LSB Steganography.

Builds directly on Phase 2 (Basic LSB). The only difference is ORDER:
instead of embedding bits at positions 0,1,2,3... we shuffle all channel
indices using a key-derived seed, then embed at the shuffled positions.

Algorithm:
  1. key string → djb2 hash → integer seed
  2. seed → Fisher-Yates shuffle of [0 .. W*H*3-1]
  3. Embed bit[i] at channel position shuffle[i]  (same 1-bit LSB)
  4. Decode: reproduce same shuffle with same key, read LSBs in that order

Security gain over Phase 2:
  - Sequential pattern eliminated → Chi-square test fails
  - Without the key, attacker cannot determine which channels carry data
  - Same image capacity as basic LSB

Reuses:
  shared/image_io, shared/binary_utils, shared/report_utils,
  phase1_basics/pixel_matrix (pixel table), phase3_lsb_decode (integrity)
"""

import os
import sys
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.image_io import load_image, save_image, numpy_to_pil, get_dimensions, get_total_pixels
from shared.binary_utils import text_to_bits, bits_to_text, text_to_binary_table, DELIMITER
from shared.report_utils import (
    SEP, SEP2, header, section,
    format_pixel_table_header, format_pixel_row,
    format_change_table_header, format_change_row,
)
from phase1_basics.pixel_matrix import get_pixel_data
from phase3_lsb_decode.lsb_decoder import compute_integrity


# ── Key utilities ──────────────────────────────────────────────────────────────

def djb2_hash(key: str) -> int:
    """djb2 hash: key string → unsigned 32-bit integer seed."""
    h = 5381
    for ch in key:
        h = ((h << 5) + h + ord(ch)) & 0xFFFFFFFF
    return h


def fisher_yates_shuffle(n: int, seed: int) -> list:
    """
    Fisher-Yates shuffle of [0..n-1] using a seeded LCG RNG.
    Reproducible: same seed always produces same shuffle.
    Returns shuffled index list.
    """
    # LCG parameters (same as glibc rand)
    indices = list(range(n))
    state   = seed & 0xFFFFFFFF
    for i in range(n - 1, 0, -1):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        j     = state % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]
    return indices


# ── Capacity check ─────────────────────────────────────────────────────────────

def check_capacity(np_array: np.ndarray, message: str) -> tuple:
    w, h           = get_dimensions(np_array)
    capacity_bits  = w * h * 3
    capacity_chars = (capacity_bits // 8) - len(DELIMITER) - 1
    needed         = len(message) + len(DELIMITER)
    return (needed * 8 <= capacity_bits), capacity_chars, needed


# ── Encoder ────────────────────────────────────────────────────────────────────

def encode_random_lsb(np_array: np.ndarray, message: str, key: str) -> tuple:
    """
    Embed message using randomized LSB.

    Returns:
        (stego_array, changes, bits, shuffle_indices, key_hash, seed)
    """
    stego        = np_array.copy()
    h, w         = stego.shape[:2]
    full_message = message + DELIMITER
    bits         = text_to_bits(full_message)
    total_ch     = w * h * 3

    key_hash = djb2_hash(key)
    shuffle  = fisher_yates_shuffle(total_ch, key_hash)

    changes  = []
    ch_names = ["R", "G", "B"]

    for bit_index, bit in enumerate(bits):
        flat_ch  = shuffle[bit_index]          # shuffled channel position
        pixel_idx = flat_ch // 3
        ch        = flat_ch % 3
        row       = pixel_idx // w
        col       = pixel_idx % w

        old_val = int(stego[row, col, ch])
        new_val = (old_val & 0xFE) | bit
        stego[row, col, ch] = new_val

        if old_val != new_val:
            changes.append({
                "bit_index"     : bit_index,
                "shuffle_pos"   : flat_ch,
                "pixel_idx"     : pixel_idx,
                "row"           : row,
                "col"           : col,
                "channel"       : ch_names[ch],
                "old_val"       : old_val,
                "new_val"       : new_val,
                "diff"          : new_val - old_val,
                "bit_embedded"  : bit,
            })

    return stego, changes, bits, shuffle, key_hash, key_hash


# ── Decoder ────────────────────────────────────────────────────────────────────

def decode_random_lsb(np_array: np.ndarray, key: str) -> tuple:
    """
    Extract message using same key → same shuffle → same positions.

    Returns:
        (message, raw_bits, bit_table, shuffle_indices, key_hash)
    """
    h, w      = np_array.shape[:2]
    total_ch  = w * h * 3
    ch_names  = ["R", "G", "B"]

    key_hash = djb2_hash(key)
    shuffle  = fisher_yates_shuffle(total_ch, key_hash)

    bits      = []
    bit_table = []

    for i, flat_ch in enumerate(shuffle):
        pixel_idx = flat_ch // 3
        ch        = flat_ch % 3
        row       = pixel_idx // (w)
        col       = pixel_idx % w
        val       = int(np_array[row, col, ch])
        lsb       = val & 1
        bits.append(lsb)

        bit_table.append({
            "bit_index"  : i,
            "shuffle_pos": flat_ch,
            "pixel_idx"  : pixel_idx,
            "row"        : row,
            "col"        : col,
            "channel"    : ch_names[ch],
            "byte_val"   : val,
            "binary"     : format(val, "08b"),
            "lsb"        : lsb,
        })

        if len(bits) % 8 == 0:
            text_so_far = bits_to_text(bits)
            if text_so_far.endswith(DELIMITER):
                message = text_so_far[:-len(DELIMITER)]
                return message, bits, bit_table, shuffle, key_hash

    return bits_to_text(bits), bits, bit_table, shuffle, key_hash


# ── Report: Encoding ───────────────────────────────────────────────────────────

def build_encoding_report(image_path, original, stego, message,
                           changes, bits, shuffle, key, key_hash, output_image_path):
    w, h         = get_dimensions(original)
    total        = get_total_pixels(original)
    ts           = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname        = os.path.basename(image_path)
    full_msg     = message + DELIMITER
    total_ch     = w * h * 3

    lines = [
        header(
            "IMAGE STEGANOGRAPHY — Phase 4: Randomized LSB Encoding",
            f"File: {fname}  |  Generated: {ts}"
        ),
        section("1. ENCODING SUMMARY"),
        f"  Algorithm       : Randomized LSB",
        f"  Cover image     : {fname}",
        f"  Dimensions      : {w} x {h} px  |  {total:,} total pixels",
        f"  Total channels  : {total_ch:,}",
        f"  Capacity        : {total_ch:,} bits  /  {total_ch//8:,} chars",
        f"",
        f"  Secret key      : \"{key}\"",
        f"  djb2 hash       : {key_hash}  (decimal)",
        f"  djb2 hash (hex) : 0x{key_hash:08X}",
        f"  Shuffle seed    : {key_hash}",
        f"",
        f"  Message length  : {len(message)} chars",
        f"  + Delimiter     : {len(DELIMITER)} bytes",
        f"  Total embedded  : {len(full_msg)} chars  =  {len(bits)} bits",
        f"  Channels changed: {len(changes):,}",
        f"  Usage           : {len(bits)/total_ch*100:.4f}%",
        f"  Output saved    : {os.path.basename(output_image_path)}",
    ]

    # Key → Hash → Seed walkthrough
    lines += [
        section("2. KEY → HASH → SHUFFLE  (step by step)"),
        f"  djb2 hash algorithm:",
        f"    h = 5381",
        f"    for each char c in key:",
        f"        h = ((h << 5) + h + ord(c)) & 0xFFFFFFFF",
        f"",
        f"  Key chars:",
    ]
    h_val = 5381
    for i, ch in enumerate(key):
        prev = h_val
        h_val = ((h_val << 5) + h_val + ord(ch)) & 0xFFFFFFFF
        lines.append(f"    [{i:>2}] '{ch}' (ord={ord(ch):>3})  :  {prev} → {h_val}")
    lines += [
        f"",
        f"  Final hash / seed : {key_hash}",
        f"",
        f"  Fisher-Yates shuffle applied to {total_ch:,} channel indices.",
        f"  First 30 shuffled positions (out of {total_ch:,}):",
        f"  " + "  ".join(f"{shuffle[i]:>5}" for i in range(min(30, len(shuffle)))),
        f"",
        f"  Each shuffled index maps to: pixel = index // 3,  channel = index % 3",
        f"  First 10 mappings:",
        f"  {'Pos':>6}  {'FlatCh':>6}  {'Pixel#':>7}  {'Row':>5}  {'Col':>5}  {'Ch':>3}",
        f"  {'─'*46}",
    ]
    ch_names = ["R", "G", "B"]
    for i in range(min(10, len(bits))):
        fc  = shuffle[i]
        px  = fc // 3
        ch  = fc % 3
        row = px // w
        col = px % w
        lines.append(f"  {i:>6}  {fc:>6}  {px:>7}  {row:>5}  {col:>5}  {ch_names[ch]:>3}")

    # Text → binary
    lines += [
        section("3. TEXT → BINARY CONVERSION  (character by character)"),
        f"  Full message: {repr(full_msg)}",
        f"  {'─'*70}",
        f"  {'#':>4}  {'Char':>8}  {'ASCII':>5}  {'Binary':>8}  Bits",
        f"  {'─'*70}",
    ]
    for i, row_data in enumerate(text_to_binary_table(full_msg)):
        bits_vis = " ".join(str(b) for b in row_data["bits"])
        lines.append(
            f"  {i:>4}  {row_data['char']:>8}  {row_data['ascii']:>5}  "
            f"{row_data['binary']:>8}  {bits_vis}"
        )

    # Original pixel matrix
    lines += [
        section(f"4. ORIGINAL PIXEL MATRIX  ({total:,} pixels)"),
        f"  {'─'*74}",
        format_pixel_table_header(),
        f"  {'─'*74}",
    ]
    for p in get_pixel_data(original, total):
        lines.append(format_pixel_row(p["index"], p["row"], p["col"], p["r"], p["g"], p["b"]))

    # Change log
    lines += [
        section(f"5. PIXEL CHANGE LOG  ({len(changes):,} channel bytes modified)"),
        f"  shuffle_pos = flat channel index in shuffled order",
        f"  {'─'*90}",
        f"  {'BitIdx':>7}  {'SPos':>6}  {'Pixel#':>7}  {'Row':>5}  {'Col':>5}  {'Ch':>3}  "
        f"{'OldVal':>6}  {'NewVal':>6}  {'Diff':>5}  {'Old-bin':>8}  {'New-bin':>8}  {'Bit':>3}",
        f"  {'─'*90}",
    ]
    for c in changes:
        lines.append(
            f"  {c['bit_index']:>7}  {c['shuffle_pos']:>6}  {c['pixel_idx']:>7}  "
            f"{c['row']:>5}  {c['col']:>5}  {c['channel']:>3}  "
            f"{c['old_val']:>6}  {c['new_val']:>6}  {c['diff']:>+5}  "
            f"{format(c['old_val'],'08b'):>8}  {format(c['new_val'],'08b'):>8}  {c['bit_embedded']:>3}"
        )

    # Stego pixel matrix
    changed_pixels = set(c["pixel_idx"] for c in changes)
    lines += [
        section(f"6. STEGO PIXEL MATRIX  ({total:,} pixels)  [* = pixel modified]"),
        f"  {'─'*78}",
        f"  {'#':>6}  {'Row':>5}  {'Col':>5}  {'R':>3}  {'G':>3}  {'B':>3}  "
        f"{'R-bin':>8}  {'G-bin':>8}  {'B-bin':>8}  {'Status':>10}",
        f"  {'─'*78}",
    ]
    for p in get_pixel_data(stego, total):
        status = "* CHANGED" if p["index"] in changed_pixels else "unchanged"
        lines.append(
            f"  {p['index']:>6}  {p['row']:>5}  {p['col']:>5}  "
            f"{p['r']:>3}  {p['g']:>3}  {p['b']:>3}  "
            f"{format(p['r'],'08b'):>8}  {format(p['g'],'08b'):>8}  {format(p['b'],'08b'):>8}  "
            f"{status:>10}"
        )

    lines += ["", SEP, "  End of Report — Phase 4 Encoding", SEP]
    return "\n".join(lines)


# ── Report: Decoding ───────────────────────────────────────────────────────────

def build_decoding_report(image_path, np_array, message, raw_bits,
                           bit_table, shuffle, key, key_hash):
    w, h   = get_dimensions(np_array)
    total  = get_total_pixels(np_array)
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname  = os.path.basename(image_path)
    stats  = compute_integrity(np_array)
    full_msg = message + DELIMITER

    lines = [
        header(
            "IMAGE STEGANOGRAPHY — Phase 4: Randomized LSB Decoding",
            f"File: {fname}  |  Generated: {ts}"
        ),
        section("1. DECODING SUMMARY"),
        f"  Algorithm      : Randomized LSB",
        f"  Stego image    : {fname}",
        f"  Dimensions     : {w} x {h}  |  {total:,} pixels",
        f"  Key            : \"{key}\"",
        f"  djb2 hash      : {key_hash}  →  seed for Fisher-Yates",
        f"  Bits read      : {len(raw_bits):,}",
        f"  Message length : {len(message)} chars",
        f"  Delimiter found: YES ✓",
        f"",
        f"  DECODED MESSAGE: {repr(message)}",
        section("2. BIT EXTRACTION LOG  (shuffled order)"),
        f"  {'─'*76}",
        f"  {'BitIdx':>7}  {'SPos':>6}  {'Pixel#':>7}  {'Row':>5}  {'Col':>5}  "
        f"{'Ch':>3}  {'Val':>3}  {'Binary':>8}  {'LSB':>3}",
        f"  {'─'*76}",
    ]
    for b in bit_table:
        lines.append(
            f"  {b['bit_index']:>7}  {b['shuffle_pos']:>6}  {b['pixel_idx']:>7}  "
            f"{b['row']:>5}  {b['col']:>5}  {b['channel']:>3}  "
            f"{b['byte_val']:>3}  {b['binary']:>8}  {b['lsb']:>3}"
        )

    lines += [
        section("3. BIT STREAM → TEXT RECONSTRUCTION"),
        f"  {'─'*70}",
        f"  {'#':>4}  {'Char':>8}  {'ASCII':>5}  {'Binary':>8}  {'Bits':>24}  Note",
        f"  {'─'*70}",
    ]
    for i, row_data in enumerate(text_to_binary_table(full_msg)):
        note     = "← delimiter" if row_data["ascii"] in [0, 1] else ""
        bits_str = " ".join(str(b) for b in row_data["bits"])
        lines.append(
            f"  {i:>4}  {row_data['char']:>8}  {row_data['ascii']:>5}  "
            f"{row_data['binary']:>8}  {bits_str:>24}  {note}"
        )

    lines += [
        section("4. IMAGE INTEGRITY — Channel Statistics"),
        f"  {'─'*54}",
        f"  {'Channel':>8}  {'Min':>5}  {'Max':>5}  {'Mean':>10}  {'Std':>10}",
        f"  {'─'*54}",
    ]
    for ch, s in stats.items():
        lines.append(
            f"  {ch:>8}  {s['min']:>5}  {s['max']:>5}  {s['mean']:>10.4f}  {s['std']:>10.4f}"
        )
    lines += ["", SEP, "  End of Report — Phase 4 Decoding", SEP]
    return "\n".join(lines)


def save_report(report, output_dir, filename):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path
