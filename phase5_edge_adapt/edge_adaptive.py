"""
phase5_edge_adapt/edge_adaptive.py
-----------------------------------
Phase 5: Edge-Adaptive Steganography.

Embeds variable bit depths (1 to 3 bits) into pixel channels based on local
luminance variance. Textured and edge regions hold more bits (up to 3 bits)
while smooth regions hold fewer (1 bit), maximizing imperceptibility.
"""

import os
import sys
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import shared
from shared.image_io import load_image, save_image, numpy_to_pil, get_dimensions, get_total_pixels
from shared.binary_utils import text_to_bits, bits_to_text, text_to_binary_table, DELIMITER
from shared.report_utils import SEP, SEP2, header, section


def compute_msb_luminance(np_array: np.ndarray) -> np.ndarray:
    """
    Compute luminance using top 5 MSBs (mask 0xF8) for stable variance.
    L = 0.299*R + 0.587*G + 0.114*B
    """
    msb_array = np_array & 0xF8
    lum = (0.299 * msb_array[:, :, 0] +
           0.587 * msb_array[:, :, 1] +
           0.114 * msb_array[:, :, 2])
    return lum


def compute_local_variance_map(np_array: np.ndarray) -> np.ndarray:
    """
    Compute 3x3 local variance across image using padded luminance.
    Returns (H, W) float array of variances.
    """
    lum = compute_msb_luminance(np_array)
    h, w = lum.shape
    padded = np.pad(lum, pad_width=1, mode='edge')
    var_map = np.zeros((h, w), dtype=np.float32)

    for r in range(h):
        for c in range(w):
            win = padded[r:r+3, c:c+3]
            var_map[r, c] = float(np.var(win))

    return var_map


def variance_to_depth(var_val: float) -> int:
    """Map variance value to embedding bit depth (1, 2, or 3 bits)."""
    if var_val < 200.0:
        return 1
    elif var_val < 800.0:
        return 2
    else:
        return 3


def check_capacity(np_array: np.ndarray, message: str) -> tuple:
    """Compute adaptive capacity based on local variance."""
    var_map = compute_local_variance_map(np_array)
    h, w = var_map.shape
    total_bits = 0
    for r in range(h):
        for c in range(w):
            d = variance_to_depth(var_map[r, c])
            total_bits += d * 3

    capacity_chars = (total_bits // 8) - len(DELIMITER) - 1
    needed = len(message) + len(DELIMITER)
    return (needed * 8 <= total_bits), capacity_chars, needed


def encode_edge_adaptive(np_array: np.ndarray, message: str) -> tuple:
    """
    Encode message adaptively based on 3x3 MSB variance map.
    Returns (stego_array, changes, bits, var_map).
    """
    stego = np_array.copy()
    h, w = stego.shape[:2]
    var_map = compute_local_variance_map(stego)

    full_message = message + DELIMITER
    bits = text_to_bits(full_message)
    bit_index = 0
    changes = []
    ch_names = ["R", "G", "B"]

    for r in range(h):
        for c in range(w):
            depth = variance_to_depth(var_map[r, c])
            mask = (~((1 << depth) - 1)) & 0xFF

            for ch in range(3):
                if bit_index >= len(bits):
                    break

                bits_to_take = min(depth, len(bits) - bit_index)
                val_to_embed = 0
                for b_i in range(bits_to_take):
                    val_to_embed = (val_to_embed << 1) | bits[bit_index + b_i]

                curr_mask = (~((1 << bits_to_take) - 1)) & 0xFF if bits_to_take < depth else mask

                old_val = int(stego[r, c, ch])
                new_val = (old_val & curr_mask) | val_to_embed
                stego[r, c, ch] = new_val

                if old_val != new_val:
                    changes.append({
                        "pixel_idx": r * w + c,
                        "row": r,
                        "col": c,
                        "channel": ch_names[ch],
                        "depth": bits_to_take,
                        "old_val": old_val,
                        "new_val": new_val,
                        "diff": new_val - old_val,
                        "bit_embedded": val_to_embed,
                    })

                bit_index += bits_to_take

            if bit_index >= len(bits):
                break
        if bit_index >= len(bits):
            break

    return stego, changes, bits, var_map


def decode_edge_adaptive(np_array: np.ndarray) -> tuple:
    """
    Extract message adaptively using same MSB variance map.
    Returns (message, bits, bit_table, var_map).
    """
    h, w = np_array.shape[:2]
    var_map = compute_local_variance_map(np_array)
    bits = []
    bit_table = []
    ch_names = ["R", "G", "B"]

    for r in range(h):
        for c in range(w):
            depth = variance_to_depth(var_map[r, c])
            mask = (1 << depth) - 1

            for ch in range(3):
                val = int(np_array[r, c, ch])
                extracted = val & mask

                for b_i in range(depth - 1, -1, -1):
                    bit = (extracted >> b_i) & 1
                    bits.append(bit)

                bit_table.append({
                    "pixel_idx": r * w + c,
                    "row": r,
                    "col": c,
                    "channel": ch_names[ch],
                    "byte_val": val,
                    "depth": depth,
                    "extracted": extracted,
                    "binary": format(val, "08b"),
                    "lsb": extracted,
                })

                # Check if delimiter is found
                if len(bits) >= 32 and len(bits) % 8 == 0:
                    text_so_far = bits_to_text(bits)
                    if DELIMITER in text_so_far:
                        message = text_so_far.split(DELIMITER, 1)[0]
                        return message, bits, bit_table, var_map

    text_so_far = bits_to_text(bits)
    if DELIMITER in text_so_far:
        message = text_so_far.split(DELIMITER, 1)[0]
    else:
        message = text_so_far
    return message, bits, bit_table, var_map


def build_encoding_report(image_path: str, original: np.ndarray, stego: np.ndarray,
                          message: str, changes: list, bits: list,
                          var_map: np.ndarray, output_image_path: str) -> str:
    w, h = get_dimensions(original)
    total = get_total_pixels(original)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname = os.path.basename(image_path)

    lines = [
        header(
            "IMAGE STEGANOGRAPHY — Phase 5: Edge-Adaptive Encoding",
            f"File: {fname}  |  Generated: {ts}"
        ),
        section("1. ENCODING SUMMARY"),
        f"  Algorithm       : Edge-Adaptive Steganography (Variance-Based Depth)",
        f"  Cover image     : {fname}",
        f"  Dimensions      : {w} x {h} px  |  {total:,} pixels",
        f"  Message length  : {len(message)} chars  (+ {len(DELIMITER)} bytes delimiter)",
        f"  Bits embedded   : {len(bits)} bits",
        f"  Channels changed: {len(changes):,}",
        f"  Variance range  : Min={float(var_map.min()):.2f}, Max={float(var_map.max()):.2f}, Mean={float(var_map.mean()):.2f}",
        f"  Output saved    : {os.path.basename(output_image_path)}",
    ]
    return "\n".join(lines)


def build_decoding_report(image_path: str, np_array: np.ndarray, message: str,
                          raw_bits: list, bit_table: list, var_map: np.ndarray) -> str:
    w, h = get_dimensions(np_array)
    total = get_total_pixels(np_array)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname = os.path.basename(image_path)

    lines = [
        header(
            "IMAGE STEGANOGRAPHY — Phase 5: Edge-Adaptive Decoding",
            f"File: {fname}  |  Generated: {ts}"
        ),
        section("1. DECODING SUMMARY"),
        f"  Algorithm      : Edge-Adaptive Steganography",
        f"  Stego image    : {fname}",
        f"  Dimensions     : {w} x {h} px  |  {total:,} pixels",
        f"  Bits read      : {len(raw_bits):,}",
        f"  Message length : {len(message)} chars",
        f"",
        f"  DECODED MESSAGE: {repr(message)}",
    ]
    return "\n".join(lines)


def save_report(report: str, output_dir: str, filename: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path
