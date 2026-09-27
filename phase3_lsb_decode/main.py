"""
phase3_lsb_decode/main.py
--------------------------
Runner for Phase 3: LSB Decoding.

Usage (from project root):
    python -m phase3_lsb_decode.main --image phase3_lsb_decode/images/input/stego.png
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import shared
from shared.image_io import load_image
from phase3_lsb_decode.lsb_decoder import decode_lsb, build_decoding_report, save_report


def parse_args():
    p = argparse.ArgumentParser(description="Phase 3 — LSB Steganography Decoder")
    p.add_argument("--image", required=True, help="Path to stego image")
    return p.parse_args()


def main():
    args       = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = args.image if os.path.isabs(args.image) else os.path.abspath(args.image)
    output_dir = os.path.join(script_dir, "images", "output")

    print(f"\n  [Phase 3] Loading stego image: {image_path}")
    try:
        _, np_array = load_image(image_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ERROR: {e}"); sys.exit(1)

    print(f"  Decoding LSB message...")
    message, raw_bits, bit_table = decode_lsb(np_array)

    print(f"\n  ✓ DECODED MESSAGE: {repr(message)}")
    print(f"  Bits read       : {len(raw_bits):,}")
    print(f"  Message length  : {len(message)} chars")

    report = build_decoding_report(image_path, np_array, message, raw_bits, bit_table)
    saved  = save_report(report, output_dir)
    print(f"  Report saved    → {saved}\n")


if __name__ == "__main__":
    main()
