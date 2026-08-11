#!/usr/bin/env python3
import json
import math
import re
import statistics
import struct
import sys
from pathlib import Path

try:
    import cv2
except Exception:
    cv2 = None


TOKEN_RE = re.compile(r"([UD])(-?\d+),(-?\d+)")
FSIZE_RE = re.compile(r"FSIZE(-?\d+),(-?\d+)")


def percentile(values, q):
    if not values:
        return 0
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return values[lo]
    return values[lo] * (hi - pos) + values[hi] * (pos - lo)


def parse_plt(path):
    text = path.read_text(errors="ignore")
    fsize = FSIZE_RE.search(text)
    sheet_w = int(fsize.group(1)) if fsize else 0
    sheet_h = int(fsize.group(2)) if fsize else 0
    contours = []
    current = []
    drawing = False

    for cmd, x_text, y_text in TOKEN_RE.findall(text):
        point = (int(x_text), int(y_text))
        if cmd == "U":
            if drawing and len(current) >= 8:
                contours.append(current)
            current = [point]
            drawing = False
        else:
            if not drawing:
                drawing = True
            current.append(point)

    if drawing and len(current) >= 8:
        contours.append(current)

    boxes = []
    for points in contours:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        if w < 80 or h < 80:
            continue
        boxes.append({
            "x": min(xs),
            "y": min(ys),
            "w": w,
            "h": h,
            "area": w * h,
            "points": len(points),
        })

    return {
        "file": str(path),
        "sheet_w": sheet_w,
        "sheet_h": sheet_h,
        "boxes": boxes,
    }


def decode_qr(path):
    if cv2 is None:
        return ""
    image = cv2.imread(str(path))
    if image is None:
        return ""
    detector = cv2.QRCodeDetector()
    height, width = image.shape[:2]
    bottom = image[int(height * 0.68):height, :]
    crops = [
        bottom[:, int(width * 0.30):int(width * 0.70)],
        bottom[:, int(width * 0.40):int(width * 0.60)],
        bottom,
    ]
    for crop in crops:
        if crop.size == 0:
            continue
        max_side = max(crop.shape[:2])
        if max_side > 1400:
            scale = 1400 / max_side
            crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        data, _, _ = detector.detectAndDecode(crop)
        data = (data or "").strip()
        if data:
            return data
    return ""


def nearest_gaps(boxes):
    gaps = []
    for i, a in enumerate(boxes):
        ax1, ay1 = a["x"], a["y"]
        ax2, ay2 = ax1 + a["w"], ay1 + a["h"]
        best = None
        for j, b in enumerate(boxes):
            if i == j:
                continue
            bx1, by1 = b["x"], b["y"]
            bx2, by2 = bx1 + b["w"], by1 + b["h"]
            dx = max(0, max(bx1 - ax2, ax1 - bx2))
            dy = max(0, max(by1 - ay2, ay1 - by2))
            distance = math.hypot(dx, dy)
            if best is None or distance < best:
                best = distance
        if best is not None:
            gaps.append(best)
    return gaps


def overlap_ratio(a0, a1, b0, b1):
    overlap = max(0, min(a1, b1) - max(a0, b0))
    base = max(1, min(a1 - a0, b1 - b0))
    return overlap / base


def cluster_count(values, tolerance):
    if not values:
        return 0
    clusters = []
    for value in sorted(values):
        if not clusters or abs(value - clusters[-1][-1]) > tolerance:
            clusters.append([value])
        else:
            clusters[-1].append(value)
    return len(clusters)


def nearest_relationships(boxes, sheet_w, sheet_h):
    relationships = []
    if len(boxes) < 2:
        return relationships
    median_long = statistics.median(max(b["w"], b["h"]) for b in boxes)
    median_short = statistics.median(min(b["w"], b["h"]) for b in boxes)
    unit = max(1.0, median_long)

    for i, a in enumerate(boxes):
        ax1, ay1 = a["x"], a["y"]
        ax2, ay2 = ax1 + a["w"], ay1 + a["h"]
        acx, acy = ax1 + a["w"] / 2, ay1 + a["h"] / 2
        best = None
        for j, b in enumerate(boxes):
            if i == j:
                continue
            bx1, by1 = b["x"], b["y"]
            bx2, by2 = bx1 + b["w"], by1 + b["h"]
            bcx, bcy = bx1 + b["w"] / 2, by1 + b["h"] / 2
            gap_x = max(0, max(bx1 - ax2, ax1 - bx2))
            gap_y = max(0, max(by1 - ay2, ay1 - by2))
            distance = math.hypot(gap_x, gap_y)
            center_dx = abs(bcx - acx)
            center_dy = abs(bcy - acy)
            candidate = {
                "distance": distance,
                "center_dx": center_dx,
                "center_dy": center_dy,
                "x_overlap": overlap_ratio(ax1, ax2, bx1, bx2),
                "y_overlap": overlap_ratio(ay1, ay2, by1, by2),
            }
            if best is None or candidate["distance"] < best["distance"]:
                best = candidate
        if best is not None:
            relationships.append({
                "distance_units": best["distance"] / unit,
                "center_dx_units": best["center_dx"] / unit,
                "center_dy_units": best["center_dy"] / unit,
                "x_overlap": best["x_overlap"],
                "y_overlap": best["y_overlap"],
                "touching": best["distance"] <= max(8.0, median_short * 0.035),
            })
    return relationships


def placement_features(boxes, sheet_w, sheet_h):
    if not boxes or sheet_w <= 0 or sheet_h <= 0:
        return {}
    median_long = statistics.median(max(b["w"], b["h"]) for b in boxes)
    median_short = statistics.median(min(b["w"], b["h"]) for b in boxes)
    edge_tolerance = max(20.0, median_short * 0.055)
    centers_x = [b["x"] + b["w"] / 2 for b in boxes]
    centers_y = [b["y"] + b["h"] / 2 for b in boxes]
    edge_hits = 0
    for b in boxes:
        if b["x"] <= edge_tolerance:
            edge_hits += 1
        if b["y"] <= edge_tolerance:
            edge_hits += 1
        if sheet_w - (b["x"] + b["w"]) <= edge_tolerance:
            edge_hits += 1
        if sheet_h - (b["y"] + b["h"]) <= edge_tolerance:
            edge_hits += 1

    rows = cluster_count(centers_y, max(1.0, median_short * 0.48))
    columns = cluster_count(centers_x, max(1.0, median_short * 0.48))
    relationships = nearest_relationships(boxes, sheet_w, sheet_h)
    return {
        "edge_pin_ratio": edge_hits / max(1, len(boxes) * 4),
        "row_count": rows,
        "column_count": columns,
        "center_spread_x": (max(centers_x) - min(centers_x)) / max(1.0, sheet_w),
        "center_spread_y": (max(centers_y) - min(centers_y)) / max(1.0, sheet_h),
        "nearest_distance_units": statistics.median([r["distance_units"] for r in relationships]) if relationships else 0,
        "nearest_dx_units": statistics.median([r["center_dx_units"] for r in relationships]) if relationships else 0,
        "nearest_dy_units": statistics.median([r["center_dy_units"] for r in relationships]) if relationships else 0,
        "nearest_x_overlap": statistics.median([r["x_overlap"] for r in relationships]) if relationships else 0,
        "nearest_y_overlap": statistics.median([r["y_overlap"] for r in relationships]) if relationships else 0,
        "touching_neighbor_ratio": sum(1 for r in relationships if r["touching"]) / max(1, len(relationships)),
    }


def orientation_features(boxes):
    if not boxes:
        return {
            "portrait_final_ratio": 0,
            "landscape_final_ratio": 0,
            "near_square_ratio": 0,
        }
    portrait = 0
    landscape = 0
    near_square = 0
    for box in boxes:
        w = box["w"]
        h = box["h"]
        if h > w * 1.08:
            portrait += 1
        elif w > h * 1.08:
            landscape += 1
        else:
            near_square += 1
    total = max(1, len(boxes))
    return {
        "portrait_final_ratio": portrait / total,
        "landscape_final_ratio": landscape / total,
        "near_square_ratio": near_square / total,
    }


def parse_tiff_layers(path):
    """Pure-stdlib reader for Photoshop layer rectangles inside TIFF tag 37724.
    Returns list of (w, h, x, y) in pixels. Handles both blob byte orders.
    No external dependency (no PIL / ImageMagick)."""
    try:
        full = open(path, "rb").read()
    except Exception:
        return []
    if full[:2] not in (b"II", b"MM"):
        return []
    tbo = "<" if full[:2] == b"II" else ">"
    try:
        u16 = lambda o: struct.unpack(tbo + "H", full[o:o + 2])[0]
        u32 = lambda o: struct.unpack(tbo + "I", full[o:o + 4])[0]
        ifd = u32(4)
        blob = None
        guard = 0
        while ifd and guard < 64:
            guard += 1
            n = u16(ifd)
            for i in range(n):
                e = ifd + 2 + i * 12
                tag = u16(e)
                cnt = u32(e + 4)
                if tag == 37724:
                    off = u32(e + 8) if cnt > 4 else e + 8
                    blob = full[off:off + cnt]
            ifd = u32(ifd + 2 + n * 12)
    except Exception:
        return []
    if not blob:
        return []
    # layer block signature follows the blob's own byte order
    if blob.find(b"8BIMLayr") >= 0 or blob.find(b"8BIMLr16") >= 0 or blob.find(b"8BIMLr32") >= 0:
        be, sig, keys = True, b"8BIM", [b"Layr", b"Lr16", b"Lr32"]
    elif blob.find(b"MIB8") >= 0:
        be, sig, keys = False, b"MIB8", [b"ryaL", b"61rL", b"23rL"]
    else:
        return []
    bb = ">" if be else "<"
    i = -1
    for k in keys:
        i = blob.find(sig + k)
        if i >= 0:
            break
    if i < 0:
        return []
    try:
        g32 = lambda o: struct.unpack(bb + "i", blob[o:o + 4])[0]
        gu32 = lambda o: struct.unpack(bb + "I", blob[o:o + 4])[0]
        gu16 = lambda o: struct.unpack(bb + "H", blob[o:o + 2])[0]
        gs16 = lambda o: struct.unpack(bb + "h", blob[o:o + 2])[0]
        p = i + 8
        gu32(p)  # section length
        p += 4
        cnt = abs(gs16(p))
        p += 2
        rects = []
        for _ in range(cnt):
            top = g32(p); left = g32(p + 4); bottom = g32(p + 8); right = g32(p + 12)
            p += 16
            nch = gu16(p); p += 2
            p += nch * 6
            p += 4 + 4 + 1 + 1 + 1 + 1  # blend sig+key, opacity, clipping, flags, filler
            extralen = gu32(p); p += 4
            p += extralen
            w = right - left
            h = bottom - top
            if w > 0 and h > 0:
                rects.append((w, h, left, top))
        return rects
    except Exception:
        return []


def tiff_figure_boxes(path):
    """A2 figure stickers only: drop background/canvas layers, icons/marks/QR, text strips."""
    layers = parse_tiff_layers(path)
    if len(layers) < 4:
        return None, None, None
    cw, ch = layers[0][0], layers[0][1]
    if cw <= 0 or ch <= 0:
        return None, None, None
    figs = []
    for w, h, x, y in layers:
        if w >= 0.55 * cw and h >= 0.55 * ch:
            continue  # background / canvas
        ls, ss = max(w, h), min(w, h)
        if ls < 300:
            continue  # icon / mark / QR (< ~25mm at 300dpi)
        if ss > 0 and ls / ss > 2.5:
            continue  # text strip
        figs.append({"w": w, "h": h, "x": x, "y": y})
    return cw, ch, figs


def main():
    if len(sys.argv) < 3:
        print("usage: analyze_manual_layouts.py <manual-folder> <output-json>", file=sys.stderr)
        return 2

    folder = Path(sys.argv[1])
    output = Path(sys.argv[2])
    cut_dir = folder / "切割文件"
    tiff_files = sorted([*folder.glob("*.tif"), *folder.glob("*.tiff")])
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    if limit > 0:
        tiff_files = tiff_files[:limit]
    files = sorted(cut_dir.glob("*.plt")) if cut_dir.exists() else sorted(folder.rglob("*.plt"))
    matched_files = []
    qr_pairs = []
    if tiff_files and cut_dir.exists():
        for tiff in tiff_files:
            code = decode_qr(tiff)
            if not code:
                continue
            plt = cut_dir / f"{code}.plt"
            if plt.exists():
                matched_files.append(plt)
                qr_pairs.append({"tiff": str(tiff), "qr": code, "plt": str(plt)})
    if matched_files:
        files = sorted(set(matched_files))
    samples = []
    all_counts = []
    all_long_sides = []
    all_short_sides = []
    all_ratios = []
    all_gaps = []
    all_coverages = []
    all_edge_pin = []
    all_rows = []
    all_columns = []
    all_spread_x = []
    all_spread_y = []
    all_nearest_distances = []
    all_nearest_dx = []
    all_nearest_dy = []
    all_nearest_x_overlap = []
    all_nearest_y_overlap = []
    all_touching_neighbor = []
    all_portrait_final = []
    all_landscape_final = []
    all_near_square = []

    for path in files:
        parsed = parse_plt(path)
        boxes = parsed["boxes"]
        if len(boxes) < 4:
            continue
        sheet_area = max(1, parsed["sheet_w"] * parsed["sheet_h"])
        box_area = sum(b["area"] for b in boxes)
        gaps = nearest_gaps(boxes)
        features = placement_features(boxes, parsed["sheet_w"], parsed["sheet_h"])
        orientation = orientation_features(boxes)
        sample = {
            "file": parsed["file"],
            "sheet": {"w": parsed["sheet_w"], "h": parsed["sheet_h"]},
            "count": len(boxes),
            "coverage_bbox": box_area / sheet_area,
            "median_long_side": statistics.median(max(b["w"], b["h"]) for b in boxes),
            "median_short_side": statistics.median(min(b["w"], b["h"]) for b in boxes),
            "median_gap": statistics.median(gaps) if gaps else 0,
            "placement": features,
            "orientation": orientation,
        }
        samples.append(sample)
        all_counts.append(len(boxes))
        all_coverages.append(sample["coverage_bbox"])
        all_gaps.extend(gaps)
        all_portrait_final.append(orientation["portrait_final_ratio"])
        all_landscape_final.append(orientation["landscape_final_ratio"])
        all_near_square.append(orientation["near_square_ratio"])
        if features:
            all_edge_pin.append(features["edge_pin_ratio"])
            all_rows.append(features["row_count"])
            all_columns.append(features["column_count"])
            all_spread_x.append(features["center_spread_x"])
            all_spread_y.append(features["center_spread_y"])
            all_nearest_distances.append(features["nearest_distance_units"])
            all_nearest_dx.append(features["nearest_dx_units"])
            all_nearest_dy.append(features["nearest_dy_units"])
            all_nearest_x_overlap.append(features["nearest_x_overlap"])
            all_nearest_y_overlap.append(features["nearest_y_overlap"])
            all_touching_neighbor.append(features["touching_neighbor_ratio"])
        for b in boxes:
            long_side = max(b["w"], b["h"])
            short_side = min(b["w"], b["h"])
            all_long_sides.append(long_side)
            all_short_sides.append(short_side)
            if short_side:
                all_ratios.append(long_side / short_side)

    # --- A2 full-coverage figure-layer pass (pure stdlib, no PIL/ImageMagick) ---
    # Overrides samples / counts / long sides / orientation using EVERY layered TIF's
    # figure layers (A2 only). placement_relationships, gaps, coverage, aspect stay
    # PLT-derived above. This is what makes the learner see ~800+ A2 samples instead
    # of only the QR<->PLT matched subset.
    DPI = 300.0
    px2mm = lambda px: px / DPI * 25.4
    tif_samples = []
    tif_counts = []
    tif_long_mm = []
    tif_portrait = []
    tif_landscape = []
    tif_square = []
    a2_scan = sorted([*folder.glob("*.tif"), *folder.glob("*.tiff")])
    for tiff in a2_scan:
        cw, ch, figs = tiff_figure_boxes(tiff)
        if not figs or len(figs) < 5:
            continue
        sheet_w_mm = round(px2mm(cw), 1)
        sheet_h_mm = round(px2mm(ch), 1)
        long_mm = max(sheet_w_mm, sheet_h_mm)
        short_mm = min(sheet_w_mm, sheet_h_mm)
        # A2 only (420 x 594 mm); skip A4 and other sizes (user no longer uses A4)
        if not (560 <= long_mm <= 620 and 400 <= short_mm <= 440):
            continue
        lss = [px2mm(max(b["w"], b["h"])) for b in figs]
        tif_samples.append({
            "file": str(tiff),
            "sheet": {"w": sheet_w_mm, "h": sheet_h_mm},
            "count": len(figs),
            "median_long_side": round(statistics.median(lss), 1),
        })
        tif_counts.append(len(figs))
        tif_long_mm.extend(round(v, 1) for v in lss)
        p = sum(1 for b in figs if b["h"] > b["w"] * 1.05) / len(figs)
        l = sum(1 for b in figs if b["w"] > b["h"] * 1.05) / len(figs)
        tif_portrait.append(p)
        tif_landscape.append(l)
        tif_square.append(max(0.0, 1.0 - p - l))

    if tif_samples:
        samples = tif_samples
        all_counts = tif_counts
        all_long_sides = tif_long_mm
        all_portrait_final = tif_portrait
        all_landscape_final = tif_landscape
        all_near_square = tif_square

    profile = {
        "version": 2,
        "source_folder": str(folder),
        "source_note": "A2-only; samples/orientation/count from layered-TIF figure layers (icons/marks/text excluded); placement_relationships from QR<->PLT pairs.",
        "sample_count": len(samples),
        "plt_count": len(files),
        "qr_pair_count": len(qr_pairs),
        "qr_pairs": qr_pairs[:300],
        "summary": {
            "items_per_sheet": {
                "p25": percentile(all_counts, 0.25),
                "median": percentile(all_counts, 0.50),
                "p75": percentile(all_counts, 0.75),
            },
            "bbox_coverage": {
                "p25": percentile(all_coverages, 0.25),
                "median": percentile(all_coverages, 0.50),
                "p75": percentile(all_coverages, 0.75),
            },
            "gap_units": {
                "p25": percentile(all_gaps, 0.25),
                "median": percentile(all_gaps, 0.50),
                "p75": percentile(all_gaps, 0.75),
            },
            "long_side_units": {
                "p25": percentile(all_long_sides, 0.25),
                "median": percentile(all_long_sides, 0.50),
                "p75": percentile(all_long_sides, 0.75),
            },
            "aspect_ratio": {
                "p25": percentile(all_ratios, 0.25),
                "median": percentile(all_ratios, 0.50),
                "p75": percentile(all_ratios, 0.75),
            },
            "orientation": {
                "portrait_final_ratio": {
                    "p25": percentile(all_portrait_final, 0.25),
                    "median": percentile(all_portrait_final, 0.50),
                    "p75": percentile(all_portrait_final, 0.75),
                },
                "landscape_final_ratio": {
                    "p25": percentile(all_landscape_final, 0.25),
                    "median": percentile(all_landscape_final, 0.50),
                    "p75": percentile(all_landscape_final, 0.75),
                },
                "near_square_ratio": {
                    "p25": percentile(all_near_square, 0.25),
                    "median": percentile(all_near_square, 0.50),
                    "p75": percentile(all_near_square, 0.75),
                },
            },
            "placement_relationships": {
                "edge_pin_ratio": {
                    "p25": percentile(all_edge_pin, 0.25),
                    "median": percentile(all_edge_pin, 0.50),
                    "p75": percentile(all_edge_pin, 0.75),
                },
                "row_count": {
                    "p25": percentile(all_rows, 0.25),
                    "median": percentile(all_rows, 0.50),
                    "p75": percentile(all_rows, 0.75),
                },
                "column_count": {
                    "p25": percentile(all_columns, 0.25),
                    "median": percentile(all_columns, 0.50),
                    "p75": percentile(all_columns, 0.75),
                },
                "center_spread_x": {
                    "p25": percentile(all_spread_x, 0.25),
                    "median": percentile(all_spread_x, 0.50),
                    "p75": percentile(all_spread_x, 0.75),
                },
                "center_spread_y": {
                    "p25": percentile(all_spread_y, 0.25),
                    "median": percentile(all_spread_y, 0.50),
                    "p75": percentile(all_spread_y, 0.75),
                },
                "nearest_distance_units": {
                    "p25": percentile(all_nearest_distances, 0.25),
                    "median": percentile(all_nearest_distances, 0.50),
                    "p75": percentile(all_nearest_distances, 0.75),
                },
                "nearest_dx_units": {
                    "p25": percentile(all_nearest_dx, 0.25),
                    "median": percentile(all_nearest_dx, 0.50),
                    "p75": percentile(all_nearest_dx, 0.75),
                },
                "nearest_dy_units": {
                    "p25": percentile(all_nearest_dy, 0.25),
                    "median": percentile(all_nearest_dy, 0.50),
                    "p75": percentile(all_nearest_dy, 0.75),
                },
                "nearest_x_overlap": {
                    "p25": percentile(all_nearest_x_overlap, 0.25),
                    "median": percentile(all_nearest_x_overlap, 0.50),
                    "p75": percentile(all_nearest_x_overlap, 0.75),
                },
                "nearest_y_overlap": {
                    "p25": percentile(all_nearest_y_overlap, 0.25),
                    "median": percentile(all_nearest_y_overlap, 0.50),
                    "p75": percentile(all_nearest_y_overlap, 0.75),
                },
                "touching_neighbor_ratio": {
                    "p25": percentile(all_touching_neighbor, 0.25),
                    "median": percentile(all_touching_neighbor, 0.50),
                    "p75": percentile(all_touching_neighbor, 0.75),
                },
            },
        },
        "samples": samples[:2000],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
    print(json.dumps(profile["summary"], ensure_ascii=False, indent=2))
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
