"""
phase2_lsb_encode/main.py
--------------------------
Runner for Phase 2: LSB Encoding.

Usage (from project root):
    python -m phase2_lsb_encode.main --image phase2_lsb_encode/images/input/sample.png --message "Hello World"
    python -m phase2_lsb_encode.main --image phase2_lsb_encode/images/input/sample.png --message "Secret" --output stego.png
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import shared
from shared.image_io import load_image, save_image, numpy_to_pil
from phase2_lsb_encode.lsb_encoder import (
    check_capacity, encode_lsb,
    build_encoding_report, save_report,
)


def parse_args():
    p = argparse.ArgumentParser(description="Phase 2 — LSB Steganography Encoder")
    p.add_argument("--image",   required=True, help="Path to cover image")
    p.add_argument("--message", required=True, help="Secret message to hide")
    p.add_argument("--output",  default="stego.png", help="Output filename (default: stego.png)")
    return p.parse_args()


def main():
    args      = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = args.image if os.path.isabs(args.image) else os.path.abspath(args.image)
    output_dir = os.path.join(script_dir, "images", "output")
    output_path = os.path.join(output_dir, args.output)

    print(f"\n  [Phase 2] Loading cover image: {image_path}")
    try:
        pil_img, np_array = load_image(image_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ERROR: {e}"); sys.exit(1)

    # Capacity check
    fits, capacity, needed = check_capacity(np_array, args.message)
    if not fits:
        print(f"  ERROR: Message too long. Capacity: {capacity} chars. Needed: {needed} chars.")
        sys.exit(1)

    print(f"  Capacity check OK  |  {needed} chars needed  /  {capacity} chars available")
    print(f"  Encoding message: {repr(args.message)}")

    # Encode
    stego_array, changes, bits = encode_lsb(np_array, args.message)

    # Save stego image
    os.makedirs(output_dir, exist_ok=True)
    stego_pil = numpy_to_pil(stego_array)
    save_image(stego_pil, output_path)
    print(f"  Stego image saved → {output_path}")
    print(f"  Pixels modified   : {len(set(c['pixel_idx'] for c in changes)):,}")
    print(f"  Channel bytes changed: {len(changes):,}")

    # Build and save report
    report = build_encoding_report(
        image_path, np_array, stego_array,
        args.message, changes, bits, output_path
    )
    saved = save_report(report, output_dir)
    print(f"  Report saved      → {saved}")
    print()
    # Print summary section only to terminal (full report in file)
    report_lines = report.split("\n")
    for line in report_lines:
        if "End of Report" in line:
            break
        if "PIXEL MATRIX" in line or "CHANGE LOG" in line:
            print(line)
            print(f"  (See full report in {os.path.basename(saved)})")
            break
        print(line)


if __name__ == "__main__":
    main()
