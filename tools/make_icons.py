#!/usr/bin/env python3
"""Draws the site's mark and writes the icon files browsers ask for.

Run by hand when the mark or the brand colour changes; the output is
committed, so the site itself still has no build step:

    python3 tools/make_icons.py

The mark is one shape defined twice — once as `favicon.svg`, which is what
the pages actually show, and once here in pixels, because a browser asking
for `/favicon.ico` will not accept an SVG and neither will an iOS home
screen. Keep the two in step: the numbers below are the same proportions
the SVG uses.

Pure standard library on purpose. A pillow dependency for four small files
that change once a year is a dependency that will be broken the next time
anyone needs them.
"""

import struct
import zlib
from pathlib import Path

# The brand colour, shared with the app's AppTheme.seed and the site's
# --accent. Change it here, in assets/style.css and in app_theme.dart
# together, or the listing page and the screenshots stop matching.
BLUE = (0x3F, 0x6E, 0x9A)
WHITE = (0xFF, 0xFF, 0xFF)

# Proportions of the tile, as fractions of its side. The corner radius is
# Apple's "squircle" territory; the letter is a plain geometric L so that
# it survives being drawn at sixteen pixels.
RADIUS = 0.22
STEM_LEFT, STEM_RIGHT = 0.34, 0.46
FOOT_RIGHT = 0.70
TOP, BOTTOM = 0.26, 0.74

# Every pixel is averaged from this many samples per side. Without it the
# rounded corners are a staircase at 16 px.
SUPERSAMPLE = 4


def _tile(size: int) -> list[list[tuple[int, int, int, int]]]:
    """The mark at [size] × [size], as RGBA rows."""
    big = size * SUPERSAMPLE
    radius = RADIUS * big

    def inside_tile(x: float, y: float) -> bool:
        # Within the square, minus the four corner circles.
        for cx, cy in (
            (radius, radius),
            (big - radius, radius),
            (radius, big - radius),
            (big - radius, big - radius),
        ):
            near_x = x < radius if cx == radius else x > big - radius
            near_y = y < radius if cy == radius else y > big - radius
            if near_x and near_y:
                return (x - cx) ** 2 + (y - cy) ** 2 <= radius**2
        return True

    def inside_letter(x: float, y: float) -> bool:
        stem = STEM_LEFT * big <= x <= STEM_RIGHT * big and TOP * big <= y <= BOTTOM * big
        foot = (
            STEM_LEFT * big <= x <= FOOT_RIGHT * big
            and (BOTTOM * big - (STEM_RIGHT - STEM_LEFT) * big) <= y <= BOTTOM * big
        )
        return stem or foot

    rows = []
    for py in range(size):
        row = []
        for px in range(size):
            r = g = b = a = 0
            for sy in range(SUPERSAMPLE):
                for sx in range(SUPERSAMPLE):
                    x = px * SUPERSAMPLE + sx + 0.5
                    y = py * SUPERSAMPLE + sy + 0.5
                    if not inside_tile(x, y):
                        continue
                    colour = WHITE if inside_letter(x, y) else BLUE
                    r += colour[0]
                    g += colour[1]
                    b += colour[2]
                    a += 255
            samples = SUPERSAMPLE**2
            if a == 0:
                row.append((0, 0, 0, 0))
            else:
                # Colour averaged over the covered samples only, alpha over
                # all of them: averaging colour over the empty ones darkens
                # every edge towards black.
                covered = a // 255
                row.append((r // covered, g // covered, b // covered, a // samples))
        rows.append(row)
    return rows


def _png(rows: list[list[tuple[int, int, int, int]]]) -> bytes:
    height = len(rows)
    width = len(rows[0])
    raw = b"".join(
        b"\x00" + bytes(channel for pixel in row for channel in pixel) for row in rows
    )

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _ico(pngs: list[tuple[int, bytes]]) -> bytes:
    """An ICO whose entries are PNGs, which every browser since IE11 reads."""
    header = struct.pack("<HHH", 0, 1, len(pngs))
    offset = len(header) + 16 * len(pngs)
    entries, payload = b"", b""
    for size, data in pngs:
        entries += struct.pack(
            "<BBBBHHII", size, size, 0, 0, 1, 32, len(data), offset + len(payload)
        )
        payload += data
    return header + entries + payload


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    (root / "apple-touch-icon.png").write_bytes(_png(_tile(180)))
    (root / "favicon.ico").write_bytes(
        _ico([(size, _png(_tile(size))) for size in (16, 32, 48)])
    )
    print("wrote apple-touch-icon.png and favicon.ico")


if __name__ == "__main__":
    main()
