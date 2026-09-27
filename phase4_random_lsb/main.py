"""
phase4_random_lsb/main.py
--------------------------
Runner for Phase 4: Randomized LSB.

Usage (from project root):
    # Encode
    python -m phase4_random_lsb.main --mode encode \
        --image phase4_random_lsb/images/input/sample.png \
        --message "Secret message" --key "mykey123"

    # Decode
    python -m phase4_random_lsb.main --mode decode \
        --image phase4_random_lsb/images/output/stego_random.png \
        --key "mykey123"
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import shared
from shared.image_io import load_image, save_image, numpy_to_pil
from phase4_random_lsb.random_lsb import (
    check_capacity, encode_random_lsb, decode_random_lsb,
    build_encoding_report, build_decoding_report, save_report,
)


def parse_args():
    p = argparse.ArgumentParser(description="Phase 4 — Randomized LSB Steganography")
    p.add_argument("--mode",    required=True, choices=["encode", "decode"])
    p.add_argument("--image",   required=True)
    p.add_argument("--message", help="Secret message (encode only)")
    p.add_argument("--key",     default="stego2024", help="Secret key (default: stego2024)")
    p.add_argument("--output",  default="stego_random.png")
    return p.parse_args()


def main():
    args       = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = args.image if os.path.isabs(args.image) else os.path.abspath(args.image)
    output_dir = os.path.join(script_dir, "images", "output")

    print(f"\n  [Phase 4] Mode: {args.mode.upper()}  |  Key: \"{args.key}\"")

    try:
        _, np_array = load_image(image_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ERROR: {e}"); sys.exit(1)

    if args.mode == "encode":
        if not args.message:
            print("  ERROR: --message required for encode mode"); sys.exit(1)

        fits, capacity, needed = check_capacity(np_array, args.message)
        if not fits:
            print(f"  ERROR: Message too long. Capacity={capacity}, Needed={needed}"); sys.exit(1)

        print(f"  Encoding: {repr(args.message)}")
        stego, changes, bits, shuffle, key_hash, _ = encode_random_lsb(np_array, args.message, args.key)

        output_path = os.path.join(output_dir, args.output)
        os.makedirs(output_dir, exist_ok=True)
        save_image(numpy_to_pil(stego), output_path)
        print(f"  Stego image saved   → {output_path}")
        print(f"  Channels changed    : {len(changes):,}")

        report = build_encoding_report(
            image_path, np_array, stego, args.message,
            changes, bits, shuffle, args.key, key_hash, output_path
        )
        saved = save_report(report, output_dir, "encoding_report.txt")
        print(f"  Report saved        → {saved}\n")

    else:  # decode
        print(f"  Decoding stego image...")
        message, raw_bits, bit_table, shuffle, key_hash = decode_random_lsb(np_array, args.key)

        print(f"\n  ✓ DECODED MESSAGE: {repr(message)}")
        print(f"  Bits read         : {len(raw_bits):,}")

        report = build_decoding_report(
            image_path, np_array, message, raw_bits,
            bit_table, shuffle, args.key, key_hash
        )
        saved = save_report(report, output_dir, "decoding_report.txt")
        print(f"  Report saved      → {saved}\n")


if __name__ == "__main__":
    main()
