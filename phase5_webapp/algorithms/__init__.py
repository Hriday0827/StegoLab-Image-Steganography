"""
webapp/algorithms/__init__.py
-----------------------------
Central import and dispatch point for all steganography algorithms:
  - Algorithm 1: Basic LSB (Sequential)
  - Algorithm 2: Randomized LSB (Key-seeded Fisher-Yates)
  - Algorithm 3: Edge-Adaptive (Variance-based multi-bit)
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import shared
from shared.image_io import load_image, save_image, numpy_to_pil, get_dimensions, get_total_pixels
from shared.binary_utils import text_to_bits, bits_to_text, text_to_binary_table, DELIMITER

# Phase 2 & 3: Basic LSB
from phase2_lsb_encode.lsb_encoder import check_capacity as lsb_check, encode_lsb
from phase3_lsb_decode.lsb_decoder import decode_lsb

# Phase 4: Randomized LSB
from phase4_random_lsb.random_lsb import (
    check_capacity as rlsb_check,
    encode_random_lsb,
    decode_random_lsb,
)

# Phase 5: Edge-Adaptive
from phase5_edge_adapt.edge_adaptive import (
    check_capacity as edge_check,
    encode_edge_adaptive,
    decode_edge_adaptive,
)
