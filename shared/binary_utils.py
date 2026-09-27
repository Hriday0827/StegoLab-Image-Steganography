"""
shared/binary_utils.py
-----------------------
Binary conversion utilities shared across all StegoLab phases.
Supports full UTF-8 Unicode (ASCII, international scripts, emojis, and symbols).
"""

# Delimiter used to mark the end of a hidden message
DELIMITER = "\x00\x01\x00\x01"


def int_to_bin(value: int, bits: int = 8) -> str:
    """Convert integer to zero-padded binary string."""
    return format(value, f"0{bits}b")


def bin_to_int(binary: str) -> int:
    """Convert binary string to integer."""
    return int(binary, 2)


def text_to_bits(text: str) -> list:
    """
    Convert text string (UTF-8) to a flat list of bits (MSB first).
    Each byte -> 8 bits.
    Returns list of ints (0 or 1).
    """
    raw_bytes = text.encode("utf-8")
    bits = []
    for byte_val in raw_bytes:
        for i in range(7, -1, -1):
            bits.append((byte_val >> i) & 1)
    return bits


def bits_to_text(bits: list) -> str:
    """
    Convert flat list of bits back to UTF-8 text string.
    Groups of 8 bits -> one byte -> decoded to UTF-8.
    """
    byte_arr = bytearray()
    for i in range(0, len(bits) - 7, 8):
        val = 0
        for b in bits[i:i+8]:
            val = (val << 1) | b
        byte_arr.append(val)
    return byte_arr.decode("utf-8", errors="replace")


def text_to_binary_table(text: str) -> list:
    """
    Build a detailed conversion table for display purposes.
    Returns list of dicts with:
        char     : representation of the character / byte
        ascii    : decimal byte value
        binary   : 8-bit binary string
        bits     : list of 8 ints
    """
    table = []
    # If text has multibyte unicode, show character level or byte level
    for ch in text:
        ch_bytes = ch.encode("utf-8")
        for b in ch_bytes:
            binary_str = format(b, "08b")
            table.append({
                "char"   : repr(ch) if len(ch_bytes) == 1 else f"{repr(ch)} (0x{b:02X})",
                "ascii"  : b,
                "binary" : binary_str,
                "bits"   : [int(bit) for bit in binary_str],
            })
    return table
