"""
run.py
------
Top-level runner for the StegoLab Project.

Usage:
    python run.py              # Launch the Web GUI Studio (default: http://127.0.0.1:5000)
    python run.py --port 8080  # Launch on custom port
    python run.py --test       # Run automated verification tests across all phases
"""

import sys
import os
import argparse

# Add repo root to Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import shared


def run_tests():
    print("\n" + "=" * 65)
    print("   🧪 Running StegoLab Automated Test Suite")
    print("=" * 65)

    sample_img = os.path.join(ROOT_DIR, "phase1_basics", "images", "input", "sample.png")
    if not os.path.exists(sample_img):
        print(f"❌ Sample image missing: {sample_img}")
        sys.exit(1)

    from shared.image_io import load_image
    from phase2_lsb_encode.lsb_encoder import encode_lsb
    from phase3_lsb_decode.lsb_decoder import decode_lsb
    from phase4_random_lsb.random_lsb import encode_random_lsb, decode_random_lsb
    from phase5_edge_adapt.edge_adaptive import encode_edge_adaptive, decode_edge_adaptive

    _, img_arr = load_image(sample_img)
    test_msg = "StegoLab Verified 2026! 🔐"

    # Test 1: Basic LSB
    print("\n[1/3] Testing Basic LSB (Sequential)...")
    stego1, changes1, bits1 = encode_lsb(img_arr, test_msg)
    dec1, _, _ = decode_lsb(stego1)
    assert dec1 == test_msg, f"Basic LSB mismatch! Got: {dec1}"
    print(f"  ✓ Basic LSB Passed ({len(changes1)} channel modifications)")

    # Test 2: Randomized LSB
    print("\n[2/3] Testing Randomized LSB (Key-based)...")
    stego2, changes2, bits2, _, _, _ = encode_random_lsb(img_arr, test_msg, "testkey42")
    dec2, _, _, _, _ = decode_random_lsb(stego2, "testkey42")
    assert dec2 == test_msg, f"Random LSB mismatch! Got: {dec2}"
    print(f"  ✓ Randomized LSB Passed ({len(changes2)} channel modifications)")

    # Test 3: Edge-Adaptive
    print("\n[3/3] Testing Edge-Adaptive (Local Variance)...")
    stego3, changes3, bits3, _ = encode_edge_adaptive(img_arr, test_msg)
    dec3, _, _, _ = decode_edge_adaptive(stego3)
    assert dec3 == test_msg, f"Edge-Adaptive mismatch! Got: {dec3}"
    print(f"  ✓ Edge-Adaptive Passed ({len(changes3)} channel modifications)")

    print("\n" + "=" * 65)
    print("   🎉 All 3 Steganography Algorithms Passed with 100% Integrity!")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="StegoLab — Image Steganography Suite")
    parser.add_argument("--test", action="store_true", help="Run automated test suite across all 3 algorithms")
    parser.add_argument("--port", type=int, default=5000, help="Port to run web app (default: 5000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    if args.test:
        run_tests()
    else:
        from phase5_webapp.app import run_server
        run_server(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
