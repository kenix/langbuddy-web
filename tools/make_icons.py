#!/usr/bin/env python3
"""Rasterises the mark into every icon file the site and the app need.

    python3 tools/make_icons.py                     # favicon.ico, apple-touch-icon.png
    python3 tools/make_icons.py --app ../../apps/wordgarner
                                                    # ... plus the iOS and Android icon sets

The mark is defined once, in SVG, at the site root: `icon.svg` is the app
icon, whose seeds carry a glyph each, and `favicon.svg` is the same drawing
with plain seeds, for the sizes where a glyph would only muddy a seed. This
script draws neither. It reads those two files and rasterises them with a
small scanline renderer, so the tab icon, the touch icon and the app icons
cannot drift from the SVG the pages show.

Sizes of 32 px and above take `icon.svg`; smaller ones take `favicon.svg`.

Pure standard library on purpose. A pillow or cairo dependency for a few
files that change once a year is a dependency that will be broken the next
time anyone needs them. The renderer understands exactly the SVG the mark
uses and nothing more: `<rect>` (with `rx`), `<circle>`, `<path>` with
M L H V C Q Z in absolute or relative form, `fill="#rrggbb"` on the element
or inherited from a `<g>`, `fill-rule`, and the root `viewBox`. Keep the
SVGs inside that subset, or extend the parser first.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
import zlib
from itertools import accumulate
from pathlib import Path
from xml.etree import ElementTree

# Every pixel is averaged from this many sub-scanlines; horizontally the
# coverage is exact. Without it the curves are a staircase at 16 px.
SUPERSAMPLE = 5

# Below this rendered size the seeds go plain: a glyph in a 16 px tab icon
# is three grey pixels that only blur the seed it sits on.
GLYPH_MIN_PX = 32

# Android's adaptive icon: both layers are 108 dp, the launcher shows the
# central 72 dp, and only a 66 dp circle of that is guaranteed to survive
# every mask. The pod's tips sit right on that circle at full size, so the
# foreground is drawn at this fraction of the visible 72 dp.
ANDROID_ADAPTIVE_DP = 108
ANDROID_VISIBLE_DP = 72
ANDROID_FOREGROUND_SCALE = 0.88
ANDROID_DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
ANDROID_LEGACY_DP = 48

KAPPA = 0.5522847498  # cubic approximation of a quarter circle

Point = tuple[float, float]
Colour = tuple[int, int, int]


# --------------------------------------------------------------- SVG parsing


class Shape:
    """One filled element: a colour, a fill rule and its sub-paths.

    A sub-path is a list of segments, each either a point (a straight line
    to it) or a cubic (three points: two controls and the end)."""

    def __init__(self, colour: Colour, evenodd: bool):
        self.colour = colour
        self.evenodd = evenodd
        self.subpaths: list[list[Point | tuple[Point, Point, Point]]] = []
        self.full_tile = False  # a rect covering the whole viewBox, i.e. the ground


def _colour(value: str) -> Colour:
    match = re.fullmatch(r"#([0-9a-fA-F]{6})", value.strip())
    if not match:
        raise ValueError(f"unsupported fill {value!r}: use #rrggbb")
    hexa = match.group(1)
    return tuple(int(hexa[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _ellipse_arc(cx: float, cy: float, rx: float, ry: float) -> list:
    """A full ellipse as four cubics, starting at the rightmost point."""
    kx, ky = KAPPA * rx, KAPPA * ry
    return [
        (cx + rx, cy),
        ((cx + rx, cy + ky), (cx + kx, cy + ry), (cx, cy + ry)),
        ((cx - kx, cy + ry), (cx - rx, cy + ky), (cx - rx, cy)),
        ((cx - rx, cy - ky), (cx - kx, cy - ry), (cx, cy - ry)),
        ((cx + kx, cy - ry), (cx + rx, cy - ky), (cx + rx, cy)),
    ]


def _rounded_rect(x: float, y: float, w: float, h: float, rx: float, ry: float) -> list:
    if rx <= 0 or ry <= 0:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    rx, ry = min(rx, w / 2), min(ry, h / 2)
    kx, ky = KAPPA * rx, KAPPA * ry
    return [
        (x + rx, y),
        (x + w - rx, y),
        ((x + w - rx + kx, y), (x + w, y + ry - ky), (x + w, y + ry)),
        (x + w, y + h - ry),
        ((x + w, y + h - ry + ky), (x + w - rx + kx, y + h), (x + w - rx, y + h)),
        (x + rx, y + h),
        ((x + rx - kx, y + h), (x, y + h - ry + ky), (x, y + h - ry)),
        (x, y + ry),
        ((x, y + ry - ky), (x + rx - kx, y), (x + rx, y)),
    ]


_TOKEN = re.compile(r"[MLHVCQZmlhvcqz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _path_data(d: str) -> list[list]:
    """M L H V C Q Z, absolute and relative, into sub-paths of segments."""
    tokens = _TOKEN.findall(d)
    subpaths: list[list] = []
    current: list = []
    start = cur = (0.0, 0.0)
    i, cmd = 0, ""

    def num() -> float:
        nonlocal i
        i += 1
        return float(tokens[i - 1])

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                if current:
                    subpaths.append(current)
                current = []
                cur = start
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            x, y = num(), num()
            cur = (cur[0] + x, cur[1] + y) if rel else (x, y)
            if current:
                subpaths.append(current)
            current = [cur]
            start = cur
            cmd = "l" if rel else "L"  # further pairs are line-tos
        elif c == "L":
            x, y = num(), num()
            cur = (cur[0] + x, cur[1] + y) if rel else (x, y)
            current.append(cur)
        elif c == "H":
            x = num()
            cur = (cur[0] + x if rel else x, cur[1])
            current.append(cur)
        elif c == "V":
            y = num()
            cur = (cur[0], cur[1] + y if rel else y)
            current.append(cur)
        elif c == "C":
            pts = [(num(), num()) for _ in range(3)]
            if rel:
                pts = [(cur[0] + px, cur[1] + py) for px, py in pts]
            current.append(tuple(pts))
            cur = pts[2]
        elif c == "Q":
            (qx, qy), (x, y) = (num(), num()), (num(), num())
            if rel:
                qx, qy, x, y = cur[0] + qx, cur[1] + qy, cur[0] + x, cur[1] + y
            c1 = (cur[0] + 2 / 3 * (qx - cur[0]), cur[1] + 2 / 3 * (qy - cur[1]))
            c2 = (x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y))
            current.append((c1, c2, (x, y)))
            cur = (x, y)
        else:
            raise ValueError(f"unsupported path command {cmd!r}")
    if current:
        subpaths.append(current)
    return subpaths


def parse_svg(path: Path) -> tuple[float, list[Shape]]:
    """The viewBox side and the filled shapes of one of the mark's SVGs."""
    root = ElementTree.parse(path).getroot()
    box = [float(v) for v in root.get("viewBox", "0 0 100 100").split()]
    if box[0] or box[1] or box[2] != box[3]:
        raise ValueError("the mark's viewBox must be square and start at 0 0")
    side = box[2]
    shapes: list[Shape] = []

    def walk(node: ElementTree.Element, fill: str | None, rule: str) -> None:
        fill = node.get("fill", fill)
        rule = node.get("fill-rule", rule)
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in ("svg", "g"):
            for child in node:
                walk(child, fill, rule)
            return
        if tag not in ("rect", "circle", "path"):
            return  # metadata, titles: nothing to draw
        if fill is None or fill == "none":
            return
        shape = Shape(_colour(fill), rule == "evenodd")
        f = lambda k, default="0": float(node.get(k, default))  # noqa: E731
        if tag == "rect":
            x, y, w, h = f("x"), f("y"), f("width"), f("height")
            rx = f("rx", node.get("ry", "0"))
            ry = f("ry", str(rx))
            shape.subpaths.append(_rounded_rect(x, y, w, h, rx, ry))
            shape.full_tile = (x, y, w, h) == (0, 0, side, side)
        elif tag == "circle":
            r = f("r")
            shape.subpaths.append(_ellipse_arc(f("cx"), f("cy"), r, r))
        else:
            shape.subpaths.extend(_path_data(node.get("d", "")))
        shapes.append(shape)

    walk(root, None, "nonzero")
    return side, shapes


# ------------------------------------------------------------- rasterising


def _flatten(subpath: list, scale: float, dx: float, dy: float) -> list[Point]:
    """A sub-path in pixel space, curves cut into short straight pieces."""
    pts: list[Point] = []
    cur: Point | None = None
    for seg in subpath:
        if isinstance(seg[0], (int, float)):
            cur = (seg[0] * scale + dx, seg[1] * scale + dy)
            pts.append(cur)
            continue
        (c1, c2, end) = seg
        p0 = cur or (c1[0] * scale + dx, c1[1] * scale + dy)
        p1 = (c1[0] * scale + dx, c1[1] * scale + dy)
        p2 = (c2[0] * scale + dx, c2[1] * scale + dy)
        p3 = (end[0] * scale + dx, end[1] * scale + dy)
        # Enough pieces that no piece is longer than ~2 px.
        approx = (
            math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
        )
        n = max(4, min(96, int(approx / 2) + 1))
        for k in range(1, n + 1):
            t = k / n
            u = 1 - t
            pts.append(
                (
                    u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
                )
            )
        cur = p3
    return pts


def _coverage(polys: list[list[Point]], size: int, evenodd: bool) -> list[list[float]]:
    """Per-pixel coverage, 0..1, of the union of closed polygons."""
    edges = []  # (ymin, ymax, x_at_ymin, dx_per_y, direction)
    for poly in polys:
        n = len(poly)
        for k in range(n):
            (x0, y0), (x1, y1) = poly[k], poly[(k + 1) % n]
            if y0 == y1:
                continue
            direction = 1
            if y0 > y1:
                x0, y0, x1, y1 = x1, y1, x0, y0
                direction = -1
            edges.append((y0, y1, x0, (x1 - x0) / (y1 - y0), direction))
    edges.sort()
    rows: list[list[float]] = []
    active: list = []
    next_edge = 0
    step = 1 / SUPERSAMPLE
    for py in range(size):
        diff = [0.0] * (size + 2)
        for sub in range(SUPERSAMPLE):
            y = py + (sub + 0.5) * step
            while next_edge < len(edges) and edges[next_edge][0] <= y:
                active.append(edges[next_edge])
                next_edge += 1
            active = [e for e in active if e[1] > y]
            if not active:
                continue
            crossings = sorted(
                (e[2] + (y - e[0]) * e[3], e[4]) for e in active if e[0] <= y
            )
            winding = 0
            span_start = 0.0
            for x, direction in crossings:
                before = winding
                winding = (winding + 1) % 2 if evenodd else winding + direction
                if before == 0 and winding != 0:
                    span_start = x
                elif before != 0 and winding == 0:
                    _add_span(diff, span_start, x, size)
        row = list(accumulate(diff))[:size]
        rows.append([min(1.0, c / SUPERSAMPLE) for c in row])
    return rows


def _add_span(diff: list[float], x0: float, x1: float, size: int) -> None:
    """Add exact horizontal coverage of [x0, x1) to a row's difference array."""
    x0, x1 = max(0.0, x0), min(float(size), x1)
    if x1 <= x0:
        return
    i0, i1 = int(x0), int(x1)
    if i0 == i1:
        diff[i0] += x1 - x0
        diff[i0 + 1] -= x1 - x0
        return
    head = i0 + 1 - x0
    diff[i0] += head
    diff[i0 + 1] -= head
    if i1 > i0 + 1:
        diff[i0 + 1] += 1
        diff[i1] -= 1
    if i1 < size:
        tail = x1 - i1
        diff[i1] += tail
        diff[i1 + 1] -= tail


def render(
    shapes: list[Shape],
    side: float,
    size: int,
    *,
    scale: float | None = None,
    offset: float = 0.0,
    square: bool = False,
    skip_ground: bool = False,
) -> list[list[tuple[int, int, int, int]]]:
    """The shapes at [size] x [size] px, as RGBA rows.

    [scale] is pixels per SVG unit (default: fill the square), [offset] the
    pixel inset of the drawing. [square] draws the ground with no rounded
    corners, for the platforms that apply their own mask and reject alpha.
    [skip_ground] leaves the ground out, for a layered icon's foreground."""
    scale = size / side if scale is None else scale
    rgb = [[(0.0, 0.0, 0.0)] * size for _ in range(size)]
    alpha = [[0.0] * size for _ in range(size)]
    for shape in shapes:
        if shape.full_tile and skip_ground:
            continue
        subpaths = shape.subpaths
        if shape.full_tile and square:
            subpaths = [[(0, 0), (side, 0), (side, side), (0, side)]]
        polys = [_flatten(sp, scale, offset, offset) for sp in subpaths]
        cover = _coverage(polys, size, shape.evenodd)
        cr, cg, cb = shape.colour
        for y in range(size):
            row_c, row_rgb, row_a = cover[y], rgb[y], alpha[y]
            for x in range(size):
                c = row_c[x]
                if c <= 0:
                    continue
                r, g, b = row_rgb[x]
                k = 1 - c
                row_rgb[x] = (cr * c + r * k, cg * c + g * k, cb * c + b * k)
                row_a[x] = c + row_a[x] * k
    out = []
    for y in range(size):
        out.append(
            [
                (int(r + 0.5), int(g + 0.5), int(b + 0.5), int(a * 255 + 0.5))
                for (r, g, b), a in zip(rgb[y], alpha[y])
            ]
        )
    return out


# ------------------------------------------------------------ file formats


def _png(rows: list[list[tuple[int, int, int, int]]]) -> bytes:
    height, width = len(rows), len(rows[0])
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
            "<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset + len(payload)
        )
        payload += data
    return header + entries + payload


# ---------------------------------------------------------------- the sets


class Mark:
    def __init__(self, root: Path):
        self.side, self.glyphs = parse_svg(root / "icon.svg")
        plain_side, self.plain = parse_svg(root / "favicon.svg")
        if plain_side != self.side:
            raise ValueError("icon.svg and favicon.svg must share a viewBox")

    def shapes(self, size: int) -> list[Shape]:
        return self.glyphs if size >= GLYPH_MIN_PX else self.plain

    def tile(self, size: int, **kw) -> bytes:
        return _png(render(self.shapes(size), self.side, size, **kw))


def write_site(mark: Mark, root: Path) -> list[Path]:
    written = []
    # iOS composites a transparent touch icon onto black, so: full bleed.
    written.append(root / "apple-touch-icon.png")
    written[-1].write_bytes(mark.tile(180, square=True))
    written.append(root / "favicon.ico")
    written[-1].write_bytes(_ico([(s, mark.tile(s)) for s in (16, 32, 48)]))
    return written


def write_ios(mark: Mark, app: Path) -> list[Path]:
    """Every entry of the asset catalogue's Contents.json, full bleed and opaque."""
    iconset = app / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    contents = json.loads((iconset / "Contents.json").read_text())
    written = []
    done: set[str] = set()
    for image in contents["images"]:
        name = image["filename"]
        if name in done:
            continue
        done.add(name)
        points = float(image["size"].split("x")[0])
        scale = int(image["scale"].rstrip("x"))
        size = round(points * scale)
        written.append(iconset / name)
        written[-1].write_bytes(mark.tile(size, square=True))
    return written


def write_android(mark: Mark, app: Path) -> list[Path]:
    res = app / "android" / "app" / "src" / "main" / "res"
    written = []
    for density, factor in ANDROID_DENSITIES.items():
        folder = res / f"mipmap-{density}"
        folder.mkdir(exist_ok=True)
        # Legacy launcher icon, for API < 26: the rounded tile.
        legacy = round(ANDROID_LEGACY_DP * factor)
        written.append(folder / "ic_launcher.png")
        written[-1].write_bytes(mark.tile(legacy))
        # Adaptive foreground: the drawing without its ground, centred and
        # shrunk into the safe zone. The ground is a colour resource.
        canvas = round(ANDROID_ADAPTIVE_DP * factor)
        drawn = ANDROID_VISIBLE_DP * ANDROID_FOREGROUND_SCALE * factor
        scale = drawn / mark.side
        offset = (canvas - drawn) / 2
        rows = render(
            mark.shapes(canvas), mark.side, canvas,
            scale=scale, offset=offset, skip_ground=True,
        )
        written.append(folder / "ic_launcher_foreground.png")
        written[-1].write_bytes(_png(rows))
    return written


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--app",
        type=Path,
        help="the Flutter app's root; also writes its iOS and Android icon sets",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    mark = Mark(root)
    written = write_site(mark, root)
    if args.app:
        app = args.app.resolve()
        written += write_ios(mark, app)
        written += write_android(mark, app)
    for path in written:
        print(path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path)


if __name__ == "__main__":
    main(sys.argv[1:])
