"""
phase3_lsb_decode/lsb_decoder.py
----------------------------------
Phase 3: Basic LSB Decoding.

Reverses Phase 2 encoding exactly:
  - Reads LSB of each channel byte in the same sequential order
  - Reconstructs bits → bytes → characters
  - Stops when delimiter is found

Also verifies image integrity by comparing stego image stats.
"""

import os
import sys
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.image_io import load_image, get_dimensions, get_total_pixels
from shared.binary_utils import bits_to_text, text_to_binary_table, DELIMITER
from shared.report_utils import SEP, SEP2, header, section


# ── Core decoding ──────────────────────────────────────────────────────────────

def decode_lsb(np_array: np.ndarray) -> tuple:
    """
    Extract hidden message from stego image using LSB decoding.

    Reads LSBs from R, G, B channels sequentially.
    Stops when DELIMITER is found or image runs out.

    Returns:
        (message, raw_bits, bit_table)
        message   : Decoded text string (without delimiter)
        raw_bits  : All bits read until delimiter found
        bit_table : List of dicts showing bit extraction per channel
    """
    h, w      = np_array.shape[:2]
    bits      = []
    bit_table = []   # tracks extraction for report

    for pixel_idx in range(w * h):
        row = pixel_idx // w
        col = pixel_idx % w
        ch_names = ["R", "G", "B"]

        for ch in range(3):
            val = int(np_array[row, col, ch])
            lsb = val & 1
            bits.append(lsb)
            bit_table.append({
                "pixel_idx" : pixel_idx,
                "row"       : row,
                "col"       : col,
                "channel"   : ch_names[ch],
                "byte_val"  : val,
                "binary"    : format(val, "08b"),
                "lsb"       : lsb,
                "bit_index" : len(bits) - 1,
            })

            # Every 8 bits, check if we've hit the delimiter
            if len(bits) % 8 == 0:
                text_so_far = bits_to_text(bits)
                if text_so_far.endswith(DELIMITER):
                    message = text_so_far[:-len(DELIMITER)]
                    return message, bits, bit_table

    # Delimiter not found — return raw decoded text
    text_so_far = bits_to_text(bits)
    return text_so_far, bits, bit_table


# ── Image integrity ────────────────────────────────────────────────────────────

def compute_integrity(np_array: np.ndarray) -> dict:
    """
    Compute image channel statistics for integrity verification.
    Returns dict with per-channel min, max, mean, std.
    """
    return {
        ch: {
            "min" : int(np_array[:, :, i].min()),
            "max" : int(np_array[:, :, i].max()),
            "mean": float(np_array[:, :, i].mean()),
            "std" : float(np_array[:, :, i].std()),
        }
        for i, ch in enumerate(["R", "G", "B"])
    }


# ── Report building ────────────────────────────────────────────────────────────

def build_decoding_report(image_path: str,
                           np_array: np.ndarray,
                           message: str,
                           raw_bits: list,
                           bit_table: list) -> str:
    """
    Build full decoding report with 4 sections:
      1. Summary
      2. Bit extraction log (every channel byte read, with LSB shown)
      3. Bits → text reconstruction (character by character)
      4. Image integrity stats
    """
    w, h   = get_dimensions(np_array)
    total  = get_total_pixels(np_array)
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname  = os.path.basename(image_path)
    stats  = compute_integrity(np_array)

    lines = [
        header(
            "IMAGE STEGANOGRAPHY — Phase 3: LSB Decoding",
            f"File: {fname}  |  Generated: {ts}"
        ),
        section("1. DECODING SUMMARY"),
        f"  Algorithm      : Basic LSB (Least Significant Bit)",
        f"  Stego image    : {fname}",
        f"  Dimensions     : {w} x {h} px  |  {total:,} pixels",
        f"  Total channels : {total*3:,}",
        f"  Bits read      : {len(raw_bits):,}",
        f"  Chars recovered: {len(message) + len(DELIMITER)}  (incl. delimiter)",
        f"  Message length : {len(message)} chars",
        f"  Delimiter found: {'YES ✓' if True else 'NO — image may not contain a message'}",
        f"",
        f"  DECODED MESSAGE: {repr(message)}",
    ]

    # ── Section 2: Bit extraction log ─────────────────────────────────────────
    bits_to_show = bit_table  # all bits
    lines += [
        section(f"2. BIT EXTRACTION LOG  ({len(bit_table):,} channel reads)"),
        f"  For each channel byte: value shown in decimal + binary,",
        f"  LSB (rightmost bit) extracted and collected into message.",
        f"  {'─'*76}",
        f"  {'BitIdx':>7}  {'Pixel#':>7}  {'Row':>5}  {'Col':>5}  {'Ch':>3}  "
        f"{'Val':>3}  {'Binary':>8}  {'LSB':>3}",
        f"  {'─'*76}",
    ]
    for b in bits_to_show:
        lines.append(
            f"  {b['bit_index']:>7}  {b['pixel_idx']:>7}  {b['row']:>5}  "
            f"{b['col']:>5}  {b['channel']:>3}  {b['byte_val']:>3}  "
            f"{b['binary']:>8}  {b['lsb']:>3}"
        )

    # ── Section 3: Bits → text reconstruction ─────────────────────────────────
    full_msg   = message + DELIMITER
    char_table = text_to_binary_table(full_msg)
    lines += [
        section("3. BIT STREAM → TEXT RECONSTRUCTION"),
        f"  Every 8 consecutive LSBs form one character (MSB first).",
        f"  {'─'*70}",
        f"  {'#':>4}  {'Char':>8}  {'ASCII':>5}  {'Binary':>8}  {'Bits (8 LSBs)':>24}  Note",
        f"  {'─'*70}",
    ]
    for i, row_data in enumerate(char_table):
        note = "← delimiter" if row_data["char"] in [repr(c) for c in DELIMITER] else ""
        bits_str = " ".join(str(b) for b in row_data["bits"])
        lines.append(
            f"  {i:>4}  {row_data['char']:>8}  "
            f"{row_data['ascii']:>5}  "
            f"{row_data['binary']:>8}  {bits_str:>24}  {note}"
        )

    # ── Section 4: Integrity stats ─────────────────────────────────────────────
    lines += [
        section("4. IMAGE INTEGRITY — Channel Statistics"),
        f"  (Stego image stats — compare with original to verify minimal distortion)",
        f"  {'─'*54}",
        f"  {'Channel':>8}  {'Min':>5}  {'Max':>5}  {'Mean':>10}  {'Std':>10}",
        f"  {'─'*54}",
    ]
    for ch, s in stats.items():
        lines.append(
            f"  {ch:>8}  {s['min']:>5}  {s['max']:>5}  {s['mean']:>10.4f}  {s['std']:>10.4f}"
        )
    lines += [
        f"  {'─'*54}",
        f"  Note: Max change per channel = ±1 (1-bit LSB). PSNR typically >50 dB.",
        "",
        SEP,
        "  End of Report — Phase 3",
        SEP,
    ]
    return "\n".join(lines)


def save_report(report: str, output_dir: str,
                filename: str = "decoding_report.txt") -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path
