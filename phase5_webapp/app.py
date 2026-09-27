"""
webapp/app.py
-------------
Flask web application for StegoLab.
Provides interactive visual steganography lab for 3 algorithms:
  1. Basic LSB (Sequential)
  2. Randomized LSB (Key-seeded Fisher-Yates)
  3. Edge-Adaptive (Variance-based multi-bit)
"""

import os
import sys
import uuid
import json
import numpy as np
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify, send_file, render_template

# ── Path setup ─────────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import shared
from phase5_webapp.algorithms import (
    load_image, save_image, numpy_to_pil, get_dimensions, get_total_pixels,
    text_to_binary_table, DELIMITER,
    lsb_check, encode_lsb, decode_lsb,
    rlsb_check, encode_random_lsb, decode_random_lsb,
    edge_check, encode_edge_adaptive, decode_edge_adaptive,
)

# ── App config ─────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB max upload

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "images", "uploads")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "images", "results")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_path(directory, prefix, ext="png"):
    return os.path.join(directory, f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}")


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sample/<name>")
def get_sample(name):
    """Serve built-in sample images for one-click testing."""
    sample_map = {
        "sample": os.path.join(ROOT, "phase1_basics", "images", "input", "sample.png"),
        "bike": os.path.join(ROOT, "phase1_basics", "images", "input", "bike.jpg"),
    }
    path = sample_map.get(name)
    if path and os.path.exists(path):
        return send_file(path)
    return jsonify({"error": "Sample image not found"}), 404


@app.route("/api/encode", methods=["POST"])
def api_encode():
    """
    Encode a message into a cover image.
    Form data:
        image   : image file
        message : text to hide
        algo    : lsb | rlsb | edge
        key     : secret key (for rlsb)
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    f = request.files["image"]
    if not f or not allowed_file(f.filename):
        return jsonify({"error": "Invalid image format. Supported formats: PNG, JPG, BMP, WebP."}), 400

    message = request.form.get("message", "").strip()
    algo = request.form.get("algo", "lsb").lower()
    key = request.form.get("key", "stego2024").strip() or "stego2024"

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Save upload
    upload_path = unique_path(UPLOAD_DIR, "cover")
    f.save(upload_path)

    try:
        _, np_array = load_image(upload_path)
    except Exception as e:
        return jsonify({"error": f"Could not load image: {e}"}), 400

    w, h = get_dimensions(np_array)
    total = get_total_pixels(np_array)

    # ── Encode ─────────────────────────────────────────────────────────────────
    try:
        if algo == "lsb":
            fits, cap, needed = lsb_check(np_array, message)
            if not fits:
                return jsonify({"error": f"Message too long. Capacity: {cap} chars, needed: {needed} chars."}), 400
            stego, changes, bits = encode_lsb(np_array, message)
            algo_label = "Basic LSB"

        elif algo == "rlsb":
            fits, cap, needed = rlsb_check(np_array, message)
            if not fits:
                return jsonify({"error": f"Message too long. Capacity: {cap} chars, needed: {needed} chars."}), 400
            stego, changes, bits, shuffle, key_hash, _ = encode_random_lsb(np_array, message, key)
            algo_label = "Randomized LSB"

        elif algo == "edge":
            fits, cap, needed = edge_check(np_array, message)
            if not fits:
                return jsonify({"error": f"Message too long. Capacity: {cap} chars, needed: {needed} chars."}), 400
            stego, changes, bits, var_map = encode_edge_adaptive(np_array, message)
            algo_label = "Edge-Adaptive"

        else:
            return jsonify({"error": f"Unknown algorithm: '{algo}'"}), 400

    except Exception as e:
        return jsonify({"error": f"Encoding failed: {e}"}), 500

    # Save stego image as PNG (lossless)
    result_path = unique_path(RESULTS_DIR, f"stego_{algo}")
    save_image(numpy_to_pil(stego), result_path)
    result_id = os.path.basename(result_path)

    # ── Build response payload ─────────────────────────────────────────────────
    full_msg = message + DELIMITER
    text_table = text_to_binary_table(full_msg[:120])

    # Compute PSNR
    mse = float(np.mean((np_array.astype(np.float64) - stego.astype(np.float64)) ** 2))
    psnr = round(10 * np.log10(255.0 ** 2 / (mse + 1e-10)), 2) if mse > 0 else 99.99

    # Pixel matrix preview
    pixel_matrix = []
    changed_set = set(c["pixel_idx"] for c in changes)
    indices_to_include = set(range(min(250, total)))
    for c in changes[:250]:
        indices_to_include.add(c["pixel_idx"])

    for idx in sorted(indices_to_include):
        row = idx // w
        col = idx % w
        orig_r, orig_g, orig_b = int(np_array[row, col, 0]), int(np_array[row, col, 1]), int(np_array[row, col, 2])
        steg_r, steg_g, steg_b = int(stego[row, col, 0]), int(stego[row, col, 1]), int(stego[row, col, 2])
        pixel_matrix.append({
            "idx": idx,
            "row": row,
            "col": col,
            "orig": [orig_r, orig_g, orig_b],
            "stego": [steg_r, steg_g, steg_b],
            "changed": idx in changed_set,
            "orig_bin": [format(orig_r, "08b"), format(orig_g, "08b"), format(orig_b, "08b")],
            "steg_bin": [format(steg_r, "08b"), format(steg_g, "08b"), format(steg_b, "08b")],
        })

    # Change log
    change_log = []
    for c in changes[:250]:
        old_val = c.get("old_val", 0)
        new_val = c.get("new_val", 0)
        change_log.append({
            "pixel_idx": c["pixel_idx"],
            "row": c["row"],
            "col": c["col"],
            "channel": c["channel"],
            "depth": c.get("depth", 1),
            "old_val": old_val,
            "new_val": new_val,
            "diff": c["diff"],
            "old_bin": format(old_val, "08b"),
            "new_bin": format(new_val, "08b"),
            "bit_embedded": c["bit_embedded"],
        })

    stats = {
        "algo": algo_label,
        "width": w,
        "height": h,
        "total_pixels": total,
        "total_channels": total * 3,
        "msg_length": len(message),
        "bits_embedded": len(bits),
        "pixels_changed": len(changed_set),
        "channels_changed": len(changes),
        "usage_pct": round(len(bits) / (total * 3) * 100, 4),
        "psnr_db": psnr,
        "key_used": key if algo == "rlsb" else None,
        "total_changes_count": len(changes),
        "preview_matrix_count": len(pixel_matrix),
    }

    return jsonify({
        "result_id": result_id,
        "stats": stats,
        "text_table": text_table,
        "change_log": change_log,
        "pixel_matrix": pixel_matrix,
    })


@app.route("/api/decode", methods=["POST"])
def api_decode():
    """
    Decode a hidden message from a stego image.
    Form data:
        image : stego image file
        algo  : lsb | rlsb | edge
        key   : secret key (for rlsb)
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    f = request.files["image"]
    if not f or not allowed_file(f.filename):
        return jsonify({"error": "Invalid image format"}), 400

    algo = request.form.get("algo", "lsb").lower()
    key = request.form.get("key", "stego2024").strip() or "stego2024"

    upload_path = unique_path(UPLOAD_DIR, "stego_in")
    f.save(upload_path)

    try:
        _, np_array = load_image(upload_path)
    except Exception as e:
        return jsonify({"error": f"Could not load image: {e}"}), 400

    try:
        delimiter_found = True
        if algo == "lsb":
            message, raw_bits, bit_table = decode_lsb(np_array)
            algo_label = "Basic LSB"
        elif algo == "rlsb":
            message, raw_bits, bit_table, _, _ = decode_random_lsb(np_array, key)
            algo_label = "Randomized LSB"
        elif algo == "edge":
            message, raw_bits, bit_table, _ = decode_edge_adaptive(np_array)
            algo_label = "Edge-Adaptive"
        else:
            return jsonify({"error": "Unknown algorithm"}), 400

    except Exception as e:
        return jsonify({"error": f"Decoding failed: {e}"}), 500

    if len(raw_bits) >= get_total_pixels(np_array) * 3 and not (message and len(message) < len(raw_bits) // 8):
        delimiter_found = False
        message = message[:120]

    full_msg = message + (DELIMITER if delimiter_found else "")
    text_table = text_to_binary_table(full_msg[:100])

    extraction_log = []
    for b in bit_table[:150]:
        byte_val = b.get("byte_val", 0)
        extraction_log.append({
            "bit_index": b.get("bit_index", 0),
            "pixel_idx": b.get("pixel_idx", 0),
            "row": b.get("row", 0),
            "col": b.get("col", 0),
            "channel": b.get("channel", "?"),
            "byte_val": byte_val,
            "binary": b.get("binary", format(byte_val, "08b")),
            "lsb": b.get("lsb", b.get("extracted", 0)),
            "depth": b.get("depth", 1),
        })

    return jsonify({
        "message": message,
        "algo_label": algo_label,
        "delimiter_found": delimiter_found,
        "bits_read": len(raw_bits),
        "msg_length": len(message),
        "text_table": text_table,
        "extraction_log": extraction_log,
    })


@app.route("/api/download/<filename>")
def download_result(filename):
    """Download encoded stego image."""
    safe = os.path.basename(filename)
    path = os.path.join(RESULTS_DIR, safe)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True, download_name=f"stego_{safe}")


def run_server(port=5000, host="127.0.0.1", debug=True):
    print("\n" + "=" * 60)
    print("   🚀 StegoLab — Interactive Steganography Studio")
    print("   3 Algorithms Active: Basic LSB, Randomized LSB, Edge-Adaptive")
    print(f"   Open: http://{host}:{port} in your browser")
    print("=" * 60 + "\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
