"""
phase1_basics/pixel_matrix.py
------------------------------
Core module for Phase 1: Image Processing Basics.

Extracts RGB pixel matrix, converts to binary, generates structured report.
All image I/O delegated to shared/image_io.py.
Functions here are reused by Phase 2+ for pixel access.
"""

import os
import sys
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.image_io import load_image, get_dimensions, get_total_pixels
from shared.report_utils import (
    SEP, SEP2, header, section,
    format_pixel_table_header, format_pixel_row,
)


def extract_pixel_matrix(np_array: np.ndarray) -> np.ndarray:
    """Return full RGB pixel matrix copy. Shape (H, W, 3)."""
    return np_array.copy()


def get_pixel_data(np_array: np.ndarray, n: int) -> list:
    """
    Extract data for the first N pixels (row-major order).
    Each dict: index, row, col, r, g, b, r_bin, g_bin, b_bin.
    """
    h, w = np_array.shape[:2]
    total = w * h
    n = min(n, total)
    pixels = []
    count = 0
    for row in range(h):
        for col in range(w):
            if count >= n:
                break
            r = int(np_array[row, col, 0])
            g = int(np_array[row, col, 1])
            b = int(np_array[row, col, 2])
            pixels.append({
                "index": count, "row": row, "col": col,
                "r": r, "g": g, "b": b,
                "r_bin": format(r, "08b"),
                "g_bin": format(g, "08b"),
                "b_bin": format(b, "08b"),
            })
            count += 1
        if count >= n:
            break
    return pixels


def build_report(image_path: str, np_array: np.ndarray, n: int) -> str:
    """Build full text report: metadata + pixel table + matrix stats."""
    w, h = get_dimensions(np_array)
    total = get_total_pixels(np_array)
    pixel_data = get_pixel_data(np_array, n)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname = os.path.basename(image_path)

    lines = [
        header(
            "IMAGE STEGANOGRAPHY — Phase 1: Image Processing Basics",
            f"File: {fname}  |  Generated: {ts}"
        ),
        section("1. IMAGE METADATA"),
        f"  Width        : {w} px",
        f"  Height       : {h} px",
        f"  Dimensions   : {w} x {h}",
        f"  Total pixels : {total:,}",
        f"  Channels     : 3  (R, G, B)",
        f"  Color depth  : 8-bit per channel  (0–255)",
        f"  Bit depth    : 24-bit per pixel",
        f"  Capacity*    : {w*h*3} bits  /  {w*h*3//8} bytes  (* for 1-bit LSB)",
        section(f"2. PIXEL DATA  —  First {len(pixel_data):,} of {total:,} pixels"),
        f"  (Row-major order: left→right, top→bottom)",
        f"  {'─'*74}",
        format_pixel_table_header(),
        f"  {'─'*74}",
    ]

    for p in pixel_data:
        lines.append(format_pixel_row(
            p["index"], p["row"], p["col"],
            p["r"], p["g"], p["b"]
        ))

    lines += [
        f"  {'─'*74}",
        section("3. RGB MATRIX SUMMARY"),
        f"  Array shape  : {np_array.shape}   (height × width × channels)",
        f"  Data type    : {np_array.dtype}",
        f"  Min value    : {int(np_array.min())}",
        f"  Max value    : {int(np_array.max())}",
        f"  Mean R       : {np_array[:,:,0].mean():.4f}",
        f"  Mean G       : {np_array[:,:,1].mean():.4f}",
        f"  Mean B       : {np_array[:,:,2].mean():.4f}",
        f"  Std R        : {np_array[:,:,0].std():.4f}",
        f"  Std G        : {np_array[:,:,1].std():.4f}",
        f"  Std B        : {np_array[:,:,2].std():.4f}",
        "",
        SEP,
        "  End of Report — Phase 1",
        SEP,
    ]
    return "\n".join(lines)


def save_report(report: str, output_dir: str,
                filename: str = "pixel_report.txt") -> str:
    """Save report to output_dir/filename. Returns saved path."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path
