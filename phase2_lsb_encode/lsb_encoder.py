"""
phase2_lsb_encode/lsb_encoder.py
----------------------------------
Phase 2: Basic LSB (Least Significant Bit) Encoding.

Algorithm:
  Each character of the message is converted to its 8-bit ASCII binary.
  Each bit is embedded into the LSB of consecutive channel bytes
  (R, G, B of pixel 0 → R, G, B of pixel 1 → ...).
  A 4-byte delimiter marks the end of the message.

Builds on Phase 1: pixel matrix extraction, binary utilities.
Produces a detailed change report showing exactly which pixels
changed, which channel, old/new values, and the bit embedded.
"""

import os
import sys
import numpy as np
from datetime import datetime
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.image_io import load_image, save_image, numpy_to_pil, get_dimensions, get_total_pixels
from shared.binary_utils import text_to_bits, text_to_binary_table, DELIMITER
from shared.report_utils import (
    SEP, SEP2, header, section,
    format_pixel_table_header, format_pixel_row,
    format_change_table_header, format_change_row,
)
from phase1_basics.pixel_matrix import extract_pixel_matrix, get_pixel_data


# ── Core encoding ──────────────────────────────────────────────────────────────

def check_capacity(np_array: np.ndarray, message: str) -> tuple:
    """
    Check if message fits in image.
    Returns (fits: bool, capacity_chars: int, needed_chars: int).
    """
    w, h = get_dimensions(np_array)
    capacity_bits  = w * h * 3
    capacity_chars = (capacity_bits // 8) - len(DELIMITER) - 1
    needed = len(message) + len(DELIMITER)
    return (needed * 8 <= capacity_bits), capacity_chars, needed


def encode_lsb(np_array: np.ndarray, message: str) -> tuple:
    """
    Embed message into image using basic LSB encoding.

    Process:
      1. Append delimiter to message
      2. Convert full message to bit stream
      3. For each bit: clear LSB of current channel byte, set it to bit value
      4. Track every change made

    Args:
        np_array : Original image array, shape (H, W, 3)
        message  : Plaintext message to hide

    Returns:
        (stego_array, changes, bit_stream)
        stego_array : Modified NumPy array
        changes     : List of change dicts (one per channel byte modified)
        bit_stream  : Full list of bits embedded
    """
    stego = np_array.copy()
    h, w  = stego.shape[:2]

    full_message = message + DELIMITER
    bits         = text_to_bits(full_message)
    bit_index    = 0
    changes      = []

    for pixel_idx in range(w * h):
        row = pixel_idx // w
        col = pixel_idx % w

        for ch in range(3):  # R=0, G=1, B=2
            if bit_index >= len(bits):
                break

            ch_names  = ["R", "G", "B"]
            old_val   = int(stego[row, col, ch])
            bit       = bits[bit_index]

            # Clear LSB and embed bit
            new_val   = (old_val & 0xFE) | bit
            stego[row, col, ch] = new_val

            if old_val != new_val:
                changes.append({
                    "pixel_idx"    : pixel_idx,
                    "row"          : row,
                    "col"          : col,
                    "channel"      : ch_names[ch],
                    "old_val"      : old_val,
                    "new_val"      : new_val,
                    "diff"         : new_val - old_val,
                    "bit_embedded" : bit,
                    "bit_index"    : bit_index,
                })

            bit_index += 1

        if bit_index >= len(bits):
            break

    return stego, changes, bits


# ── Report building ────────────────────────────────────────────────────────────

def build_encoding_report(image_path: str,
                           original: np.ndarray,
                           stego: np.ndarray,
                           message: str,
                           changes: list,
                           bits: list,
                           output_image_path: str) -> str:
    """
    Build full encoding report with 5 sections:
      1. Summary
      2. Text → Binary conversion table (every character)
      3. Original pixel matrix (all pixels)
      4. Pixel change log (every modified channel byte)
      5. Stego pixel matrix (all pixels, changed values marked)
    """
    w, h   = get_dimensions(original)
    total  = get_total_pixels(original)
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname  = os.path.basename(image_path)
    full_msg = message + DELIMITER

    # ── Section 1: Summary ─────────────────────────────────────────────────────
    lines = [
        header(
            "IMAGE STEGANOGRAPHY — Phase 2: LSB Encoding",
            f"File: {fname}  |  Generated: {ts}"
        ),
        section("1. ENCODING SUMMARY"),
        f"  Algorithm       : Basic LSB (Least Significant Bit)",
        f"  Cover image     : {fname}",
        f"  Dimensions      : {w} x {h} px",
        f"  Total pixels    : {total:,}",
        f"  Total channels  : {total*3:,}  (R, G, B per pixel)",
        f"  Capacity        : {total*3:,} bits  /  {total*3//8:,} chars",
        f"",
        f"  Message length  : {len(message)} chars",
        f"  Delimiter       : {len(DELIMITER)} bytes  (\\x00\\x01\\x00\\x01)",
        f"  Total embedded  : {len(full_msg)} chars  =  {len(bits)} bits",
        f"  Pixels used     : {(len(bits)+2)//3:,}  of  {total:,}",
        f"  Channels changed: {len(changes):,}",
        f"  Usage           : {len(bits)/(total*3)*100:.4f}%",
        f"  Output saved    : {os.path.basename(output_image_path)}",
    ]

    # ── Section 2: Text → Binary conversion ───────────────────────────────────
    lines += [
        section("2. TEXT → BINARY CONVERSION  (character by character)"),
        f"  Full message embedded: {repr(full_msg)}",
        f"  {'─'*70}",
        f"  {'#':>4}  {'Char':>8}  {'ASCII':>5}  {'Binary':>8}  Bits",
        f"  {'─'*70}",
    ]
    table = text_to_binary_table(full_msg)
    for i, row_data in enumerate(table):
        bits_visual = " ".join(str(b) for b in row_data["bits"])
        lines.append(
            f"  {i:>4}  {row_data['char']:>8}  "
            f"{row_data['ascii']:>5}  "
            f"{row_data['binary']:>8}  {bits_visual}"
        )

    # ── Section 3: Original pixel matrix ──────────────────────────────────────
    lines += [
        section(f"3. ORIGINAL PIXEL MATRIX  ({total:,} pixels)"),
        f"  {'─'*74}",
        format_pixel_table_header(),
        f"  {'─'*74}",
    ]
    orig_pixels = get_pixel_data(original, total)
    for p in orig_pixels:
        lines.append(format_pixel_row(
            p["index"], p["row"], p["col"], p["r"], p["g"], p["b"]
        ))

    # ── Section 4: Change log ──────────────────────────────────────────────────
    lines += [
        section(f"4. PIXEL CHANGE LOG  ({len(changes):,} channel bytes modified)"),
        f"  Each row = one channel byte that was changed by the LSB operation.",
        f"  Diff = NewVal - OldVal  (always -1, 0, or +1 for 1-bit LSB)",
        f"  {'─'*82}",
        format_change_table_header(),
        f"  {'─'*82}",
    ]
    for c in changes:
        lines.append(format_change_row(
            c["pixel_idx"], c["row"], c["col"], c["channel"],
            c["old_val"], c["new_val"], c["bit_embedded"]
        ))

    # ── Section 5: Stego pixel matrix ─────────────────────────────────────────
    changed_pixels = set(c["pixel_idx"] for c in changes)
    lines += [
        section(f"5. STEGO PIXEL MATRIX  ({total:,} pixels)  [* = pixel modified]"),
        f"  {'─'*78}",
        f"  {'#':>6}  {'Row':>5}  {'Col':>5}  "
        f"{'R':>3}  {'G':>3}  {'B':>3}  "
        f"{'R-bin':>8}  {'G-bin':>8}  {'B-bin':>8}  {'Status':>10}",
        f"  {'─'*78}",
    ]
    stego_pixels = get_pixel_data(stego, total)
    for p in stego_pixels:
        status = "* CHANGED" if p["index"] in changed_pixels else "unchanged"
        lines.append(
            f"  {p['index']:>6}  {p['row']:>5}  {p['col']:>5}  "
            f"{p['r']:>3}  {p['g']:>3}  {p['b']:>3}  "
            f"{format(p['r'],'08b'):>8}  {format(p['g'],'08b'):>8}  {format(p['b'],'08b'):>8}  "
            f"{status:>10}"
        )

    lines += ["", SEP, "  End of Report — Phase 2", SEP]
    return "\n".join(lines)


def save_report(report: str, output_dir: str,
                filename: str = "encoding_report.txt") -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path
