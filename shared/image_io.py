"""
shared/image_io.py
------------------
Reusable image I/O utilities used by every StegoLab phase.
"""

import os
import numpy as np
from PIL import Image


def load_image(path: str) -> tuple:
    """
    Load image from disk. Returns (PIL Image, NumPy array).
    Array shape: (H, W, 3), dtype uint8, RGB.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")
    try:
        pil_image = Image.open(path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Could not open image '{path}': {e}")
    return pil_image, np.array(pil_image, dtype=np.uint8)


def save_image(pil_image: Image.Image, path: str) -> None:
    """Save a PIL Image to disk. Creates parent dirs if needed."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    try:
        pil_image.save(path)
    except Exception as e:
        raise ValueError(f"Could not save image to '{path}': {e}")


def numpy_to_pil(np_array: np.ndarray) -> Image.Image:
    """Convert NumPy (H,W,3) uint8 array back to PIL Image."""
    return Image.fromarray(np_array.astype(np.uint8))


def get_dimensions(np_array: np.ndarray) -> tuple:
    """Return (width, height) from array shape."""
    h, w = np_array.shape[:2]
    return w, h


def get_total_pixels(np_array: np.ndarray) -> int:
    """Return total pixel count."""
    h, w = np_array.shape[:2]
    return w * h
