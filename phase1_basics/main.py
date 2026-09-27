"""
phase1_basics/main.py
---------------------
Runner for Phase 1: Image Processing Basics.

Usage (from project root):
    python -m phase1_basics.main --image phase1_basics/images/input/sample.png
    python -m phase1_basics.main --image phase1_basics/images/input/sample.png --pixels 25
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import shared
from shared.image_io import load_image, get_dimensions, get_total_pixels
from phase1_basics.pixel_matrix import extract_pixel_matrix, build_report, save_report


def parse_args():
    p = argparse.ArgumentParser(description="Phase 1 — Image pixel matrix extractor")
    p.add_argument("--image",  required=True, help="Path to input image")
    p.add_argument("--pixels", type=int, default=10,
                   help="Number of pixels to show in report (default: 10)")
    return p.parse_args()


def main():
    args = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = args.image if os.path.isabs(args.image) else os.path.abspath(args.image)
    output_dir = os.path.join(script_dir, "images", "output")

    print(f"\n  [Phase 1] Loading: {image_path}")
    try:
        pil_img, np_array = load_image(image_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    matrix = extract_pixel_matrix(np_array)
    w, h   = get_dimensions(matrix)
    total  = get_total_pixels(matrix)

    print(f"  Loaded OK  |  {w} x {h} px  |  {total:,} total pixels")
    print(f"  Showing first {min(args.pixels, total)} pixels in report...\n")

    report = build_report(image_path, matrix, args.pixels)
    print(report)

    saved = save_report(report, output_dir)
    print(f"\n  Report saved → {saved}\n")


if __name__ == "__main__":
    main()
