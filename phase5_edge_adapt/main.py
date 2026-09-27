"""
phase5_edge_adapt/main.py
-------------------------
Runner for Phase 5: Edge-Adaptive Steganography.

Usage (from project root):
    # Encode
    python -m phase5_edge_adapt.main --mode encode \
        --image phase5_edge_adapt/images/input/sample.png \
        --message "Adaptive hidden message"

    # Decode
    python -m phase5_edge_adapt.main --mode decode \
        --image phase5_edge_adapt/images/output/stego_edge.png
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import shared
from shared.image_io import load_image, save_image, numpy_to_pil
from phase5_edge_adapt.edge_adaptive import (
    check_capacity, encode_edge_adaptive, decode_edge_adaptive,
    build_encoding_report, build_decoding_report, save_report
)


def parse_args():
    p = argparse.ArgumentParser(description="Phase 5 — Edge-Adaptive Steganography")
    p.add_argument("--mode", required=True, choices=["encode", "decode"])
    p.add_argument("--image", required=True)
    p.add_argument("--message", help="Secret message (encode only)")
    p.add_argument("--output", default="stego_edge.png")
    return p.parse_args()


def main():
    args = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = args.image if os.path.isabs(args.image) else os.path.abspath(args.image)
    output_dir = os.path.join(script_dir, "images", "output")

    print(f"\n  [Phase 5] Mode: {args.mode.upper()}")

    try:
        _, np_array = load_image(image_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    if args.mode == "encode":
        if not args.message:
            print("  ERROR: --message required for encode mode")
            sys.exit(1)

        fits, capacity, needed = check_capacity(np_array, args.message)
        if not fits:
            print(f"  ERROR: Message too long. Capacity={capacity}, Needed={needed}")
            sys.exit(1)

        print(f"  Encoding: {repr(args.message)}")
        stego, changes, bits, var_map = encode_edge_adaptive(np_array, args.message)

        output_path = os.path.join(output_dir, args.output)
        os.makedirs(output_dir, exist_ok=True)
        save_image(numpy_to_pil(stego), output_path)
        print(f"  Stego image saved   → {output_path}")
        print(f"  Channels changed    : {len(changes):,}")

        report = build_encoding_report(
            image_path, np_array, stego, args.message,
            changes, bits, var_map, output_path
        )
        saved = save_report(report, output_dir, "encoding_report.txt")
        print(f"  Report saved        → {saved}\n")

    else:
        print("  Decoding edge-adaptive stego image...")
        message, raw_bits, bit_table, var_map = decode_edge_adaptive(np_array)

        print(f"\n  ✓ DECODED MESSAGE: {repr(message)}")
        print(f"  Bits read         : {len(raw_bits):,}")

        report = build_decoding_report(
            image_path, np_array, message, raw_bits, bit_table, var_map
        )
        saved = save_report(report, output_dir, "decoding_report.txt")
        print(f"  Report saved      → {saved}\n")


if __name__ == "__main__":
    main()
