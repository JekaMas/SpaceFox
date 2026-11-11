# SPDX-License-Identifier: MIT
"""Independent native PNG decoding/counting; no production pixel-counter import."""
import base64, hashlib, json, struct, sys, zlib
from pathlib import Path

def decode_png(blob):
    assert blob[:8] == b'\x89PNG\r\n\x1a\n'
    offset, compressed = 8, bytearray()
    while offset < len(blob):
        n = struct.unpack('>I', blob[offset:offset+4])[0]
        kind = blob[offset+4:offset+8]
        payload = blob[offset+8:offset+8+n]
        crc = struct.unpack('>I', blob[offset+8+n:offset+12+n])[0]
        assert zlib.crc32(kind+payload) & 0xffffffff == crc
        offset += n + 12
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', payload)
        if kind == b'IDAT': compressed.extend(payload)
    assert depth == 8 and color in (2, 6) and interlace == compression == filtering == 0
    channels = 3 if color == 2 else 4
    stride, source, rows, offset = width*channels, zlib.decompress(compressed), [], 0
    previous = bytearray(stride)
    for _ in range(height):
        filter_type = source[offset]
        row = bytearray(source[offset+1:offset+1+stride])
        offset += stride+1
        assert filter_type in range(5)
        for i in range(stride):
            left = row[i-channels] if i >= channels else 0
            above = previous[i]
            upper_left = previous[i-channels] if i >= channels else 0
            if filter_type == 0: predictor = 0
            elif filter_type == 1: predictor = left
            elif filter_type == 2: predictor = above
            elif filter_type == 3: predictor = (left+above)//2
            else:
                estimate = left+above-upper_left
                a,b,c = abs(estimate-left),abs(estimate-above),abs(estimate-upper_left)
                predictor = left if a <= b and a <= c else above if b <= c else upper_left
            row[i] = (row[i]+predictor) & 255
        rows.append(row)
        previous = row
    assert offset == len(source)
    return width, height, channels, rows

