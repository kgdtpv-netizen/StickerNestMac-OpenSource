#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path


def number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def integer(value, default=0):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def swift_round(value):
    try:
        return int(float(value) + 0.5)
    except (TypeError, ValueError):
        return 0


def swift_sheet_grid(layout, cell):
    dpi = number(layout.get("dpi"), 0.0)
    paper_w = number(layout.get("paper_w_mm"), 0.0)
    paper_h = number(layout.get("paper_h_mm"), 0.0)
    if dpi > 0 and paper_w > 0 and paper_h > 0:
        px_per_mm = dpi / 25.4
        return (
            max(1, swift_round(paper_w * px_per_mm) // cell),
            max(1, swift_round(paper_h * px_per_mm) // cell),
        )
    sheet_w_px = integer(layout.get("sheet_w_px"), 0)
    sheet_h_px = integer(layout.get("sheet_h_px"), 0)
    if sheet_w_px > 0 and sheet_h_px > 0:
        return max(1, sheet_w_px // cell), max(1, sheet_h_px // cell)
    return 0, 0


def swift_template_reserved(grid_w, grid_h):
    occupied = {}
    if grid_w <= 0 or grid_h <= 0:
        return occupied

    def fill_rect(x0, y0, x1, y1, label):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(grid_w, x1)
        y1 = min(grid_h, y1)
        for y in range(y0, y1):
            for x in range(x0, x1):
                occupied[(x, y)] = label

    if abs(grid_w - 992) <= 2 and abs(grid_h - 1403) <= 2:
        edge = 3
    else:
        edge = min(6, max(2, min(grid_w, grid_h) // 160))
    if edge > 0:
        fill_rect(0, 0, grid_w, edge, "__reserved__")
        fill_rect(0, max(0, grid_h - edge), grid_w, grid_h, "__reserved__")
        fill_rect(0, 0, edge, grid_h, "__reserved__")
        fill_rect(max(0, grid_w - edge), 0, grid_w, grid_h, "__reserved__")

    if abs(grid_w - 992) <= 2 and abs(grid_h - 1403) <= 2:
        for px_x, px_y, px_w, px_h, pad in [
            (106, 106, 224, 224, 45),
            (4630, 106, 224, 224, 45),
            (106, 6686, 224, 224, 45),
            (4630, 6686, 224, 224, 45),
            (2399, 6806, 169, 168, 130),
        ]:
            fill_rect(
                int((px_x - pad) // 5),
                int((px_y - pad) // 5),
                int(((px_x + px_w + pad) + 4) // 5),
                int(((px_y + px_h + pad) + 4) // 5),
                "__reserved__",
            )
    return occupied


def replay_swift_square_mask_runs(layout):
    cell = 5
    default_downsample = max(1, integer(layout.get("mask_downsample"), 20))
    placements = layout.get("placements") or []
    grid_w, grid_h = swift_sheet_grid(layout, cell)
    dynamic_grid = grid_w <= 0 or grid_h <= 0
    if dynamic_grid:
        grid_w = 0
        grid_h = 0
        for placement in placements:
            down = max(1, integer(placement.get("mask_downsample"), default_downsample))
            mask_w = integer(placement.get("mask_w"), 0)
            mask_h = integer(placement.get("mask_h"), 0)
            if mask_w <= 0 or mask_h <= 0:
                for run in placement.get("mask_runs") or []:
                    mask_w = max(mask_w, integer(run.get("x1")))
                    mask_h = max(mask_h, integer(run.get("y")) + 1)
            bx = swift_round(number(placement.get("mask_x")) / cell)
            by = swift_round(number(placement.get("mask_y")) / cell)
            grid_w = max(grid_w, bx + int((mask_w * down + cell - 1) // cell))
            grid_h = max(grid_h, by + int((mask_h * down + cell - 1) // cell))

    occupied = swift_template_reserved(grid_w, grid_h)
    overlap_pairs = defaultdict(int)
    overlap_cells = 0
    out_of_bounds = 0
    occupied_cells = 0

    for index, placement in enumerate(placements):
        name = str(placement.get("name") or index)
        down = max(1, integer(placement.get("mask_downsample"), default_downsample))
        mask_w = integer(placement.get("mask_w"), 0)
        mask_h = integer(placement.get("mask_h"), 0)
        if mask_w <= 0 or mask_h <= 0:
            for run in placement.get("mask_runs") or []:
                mask_w = max(mask_w, integer(run.get("x1")))
                mask_h = max(mask_h, integer(run.get("y")) + 1)
        variant_w = max(1, int((mask_w * down + cell - 1) // cell))
        variant_h = max(1, int((mask_h * down + cell - 1) // cell))
        max_x = max(0, grid_w - variant_w)
        max_y = max(0, grid_h - variant_h)
        bx = swift_round(number(placement.get("mask_x")) / cell)
        by = swift_round(number(placement.get("mask_y")) / cell)
        if not dynamic_grid:
            bx = min(max(0, bx), max_x)
            by = min(max(0, by), max_y)

        seen_in_piece = set()
        for run in placement.get("mask_runs") or []:
            y0 = max(0, int((integer(run.get("y")) * down) // cell))
            y1 = min(variant_h, int(((integer(run.get("y")) + 1) * down + cell - 1) // cell))
            x0 = max(0, int((integer(run.get("x0")) * down) // cell))
            x1 = min(variant_w, int((integer(run.get("x1")) * down + cell - 1) // cell))
            for local_y in range(y0, y1):
                y = by + local_y
                for local_x in range(x0, x1):
                    x = bx + local_x
                    if y < 0 or y >= grid_h or x < 0 or x >= grid_w:
                        out_of_bounds += 1
                        continue
                    key = (x, y)
                    if key in seen_in_piece:
                        continue
                    seen_in_piece.add(key)
                    if key in occupied:
                        overlap_cells += 1
                        pair = tuple(sorted((occupied[key], name)))
                        overlap_pairs[pair] += 1
                    else:
                        occupied[key] = name
                        occupied_cells += 1

    return {
        "grid_w": grid_w,
        "grid_h": grid_h,
        "occupied_cells": occupied_cells,
        "out_of_bounds": out_of_bounds,
        "overlap_cells": overlap_cells,
        "overlap_pairs": {" | ".join(pair): count for pair, count in sorted(overlap_pairs.items())},
    }


def replay_mask_runs(layout):
    if str(layout.get("gap_model") or "") == "swift_square":
        return replay_swift_square_mask_runs(layout)

    down = max(1, integer(layout.get("mask_downsample"), 20))
    placements = layout.get("placements") or []
    sheet_w_px = integer(layout.get("sheet_w_px"), 0)
    sheet_h_px = integer(layout.get("sheet_h_px"), 0)
    if sheet_w_px > 0 and sheet_h_px > 0:
        grid_w = (sheet_w_px + down - 1) // down
        grid_h = (sheet_h_px + down - 1) // down
    else:
        grid_w = 0
        grid_h = 0
        for placement in placements:
            px_down = max(1, integer(placement.get("mask_downsample"), down))
            bx = integer(number(placement.get("mask_x")) / px_down)
            by = integer(number(placement.get("mask_y")) / px_down)
            for run in placement.get("mask_runs") or []:
                grid_w = max(grid_w, bx + integer(run.get("x1")))
                grid_h = max(grid_h, by + integer(run.get("y")) + 1)

    occupied = {}
    overlap_pairs = defaultdict(int)
    overlap_cells = 0
    out_of_bounds = 0
    occupied_cells = 0

    for index, placement in enumerate(placements):
        name = str(placement.get("name") or index)
        px_down = max(1, integer(placement.get("mask_downsample"), down))
        bx = integer(number(placement.get("mask_x")) / px_down)
        by = integer(number(placement.get("mask_y")) / px_down)
        seen_in_piece = set()
        for run in placement.get("mask_runs") or []:
            y = by + integer(run.get("y"))
            x0 = bx + integer(run.get("x0"))
            x1 = bx + integer(run.get("x1"))
            if y < 0 or y >= grid_h:
                out_of_bounds += max(0, x1 - x0)
                continue
            for x in range(x0, x1):
                if x < 0 or x >= grid_w:
                    out_of_bounds += 1
                    continue
                key = (x, y)
                if key in seen_in_piece:
                    continue
                seen_in_piece.add(key)
                if key in occupied:
                    overlap_cells += 1
                    pair = tuple(sorted((occupied[key], name)))
                    overlap_pairs[pair] += 1
                else:
                    occupied[key] = name
                    occupied_cells += 1

    return {
        "grid_w": grid_w,
        "grid_h": grid_h,
        "occupied_cells": occupied_cells,
        "out_of_bounds": out_of_bounds,
        "overlap_cells": overlap_cells,
        "overlap_pairs": {" | ".join(pair): count for pair, count in sorted(overlap_pairs.items())},
    }


def orientation_summary(layout):
    stats = layout.get("orientation_stats") or {}
    return {
        "readable": integer(stats.get("readable"), 0),
        "upright": integer(stats.get("upright"), 0),
        "small": integer(stats.get("small"), 0),
        "upside": integer(stats.get("upside"), 0),
        "sideways": integer(stats.get("sideways"), 0),
        "hard": integer(stats.get("hard"), 0),
    }


def evaluate(layout, args):
    placements = layout.get("placements") or []
    placement_count = len(placements)
    count_field = layout.get("count")
    alpha = number(layout.get("alpha"), 0.0)
    bbox = number(layout.get("coverage_bbox"), 0.0)
    quality = number(layout.get("quality_score"), 0.0)
    replay = replay_mask_runs(layout)
    orient = orientation_summary(layout)

    failures = []
    if args.min_count is not None and placement_count < args.min_count:
        failures.append(f"count {placement_count} < min_count {args.min_count}")
    if count_field is not None and integer(count_field) != placement_count:
        failures.append(f"count_field {integer(count_field)} != placements {placement_count}")
    if args.min_alpha is not None and alpha < args.min_alpha:
        failures.append(f"alpha {alpha:.4f} < min_alpha {args.min_alpha:.4f}")
    if args.min_bbox is not None and bbox < args.min_bbox:
        failures.append(f"bbox {bbox:.4f} < min_bbox {args.min_bbox:.4f}")
    if args.max_bbox is not None and bbox > args.max_bbox:
        failures.append(f"bbox {bbox:.4f} > max_bbox {args.max_bbox:.4f}")
    if replay["out_of_bounds"] > args.max_out_of_bounds:
        failures.append(f"out_of_bounds {replay['out_of_bounds']} > {args.max_out_of_bounds}")
    if replay["overlap_cells"] > args.max_overlap_cells:
        failures.append(f"overlap_cells {replay['overlap_cells']} > {args.max_overlap_cells}")
    if args.strict_readable:
        if orient["readable"] != placement_count:
            failures.append(f"readable {orient['readable']} != placements {placement_count}")
        if orient["upside"] != 0:
            failures.append(f"upside {orient['upside']} != 0")
        if orient["sideways"] != 0:
            failures.append(f"sideways {orient['sideways']} != 0")
        if orient["hard"] != 0:
            failures.append(f"hard {orient['hard']} != 0")
    if args.max_upside is not None and orient["upside"] > args.max_upside:
        failures.append(f"upside {orient['upside']} > {args.max_upside}")
    if args.max_sideways is not None and orient["sideways"] > args.max_sideways:
        failures.append(f"sideways {orient['sideways']} > {args.max_sideways}")
    if args.max_hard is not None and orient["hard"] > args.max_hard:
        failures.append(f"hard {orient['hard']} > {args.max_hard}")

    right_center_gate = bool(layout.get("right_center_void_relocate"))
    right_center_applied = bool(layout.get("right_center_void_relocate_applied"))
    right_center_gain = number(layout.get("right_center_void_relocate_gain"), 0.0)
    if args.expect_right_center == "off" and (right_center_gate or right_center_applied):
        failures.append(
            "right_center_void_relocate enabled/applied on a layout expected to keep it off"
        )
    if args.expect_right_center == "on" and not right_center_applied:
        failures.append("right_center_void_relocate_applied is false")
    if args.min_right_center_gain is not None and right_center_gain < args.min_right_center_gain:
        failures.append(
            f"right_center_void_relocate_gain {right_center_gain:.4f} < {args.min_right_center_gain:.4f}"
        )

    right_center_chain_gate = bool(layout.get("right_center_void_chain_relocate"))
    right_center_chain_applied = bool(layout.get("right_center_void_chain_relocate_applied"))
    right_center_chain_base_applied = bool(layout.get("right_center_void_chain_relocate_base_applied"))
    right_center_chain_ever_applied = bool(
        layout.get("right_center_void_chain_relocate_ever_applied")
        or right_center_chain_applied
        or right_center_chain_base_applied
    )
    right_center_chain_alpha_gain = number(layout.get("right_center_void_chain_relocate_alpha_gain"), 0.0)
    right_center_chain_void_gain = number(layout.get("right_center_void_chain_relocate_void_gain"), 0.0)
    right_center_chain_ever_alpha_gain = number(
        layout.get("right_center_void_chain_relocate_ever_alpha_gain"),
        right_center_chain_alpha_gain,
    )
    right_center_chain_ever_void_gain = number(
        layout.get("right_center_void_chain_relocate_ever_void_gain"),
        right_center_chain_void_gain,
    )
    if args.expect_right_center_chain == "off" and (
        right_center_chain_gate or right_center_chain_applied or right_center_chain_ever_applied
    ):
        failures.append(
            "right_center_void_chain_relocate enabled/applied on a layout expected to keep it off"
        )
    if args.expect_right_center_chain == "on" and not right_center_chain_ever_applied:
        failures.append("right_center_void_chain_relocate_ever_applied is false")
    if (
        args.min_right_center_chain_alpha_gain is not None
        and right_center_chain_ever_alpha_gain < args.min_right_center_chain_alpha_gain
    ):
        failures.append(
            f"right_center_void_chain_relocate_ever_alpha_gain {right_center_chain_ever_alpha_gain:.4f} < {args.min_right_center_chain_alpha_gain:.4f}"
        )
    if (
        args.min_right_center_chain_void_gain is not None
        and right_center_chain_ever_void_gain < args.min_right_center_chain_void_gain
    ):
        failures.append(
            f"right_center_void_chain_relocate_ever_void_gain {right_center_chain_ever_void_gain:.4f} < {args.min_right_center_chain_void_gain:.4f}"
        )

    right_center_chain_second_gate = bool(layout.get("right_center_void_chain_second_backfill"))
    right_center_chain_second_applied = bool(layout.get("right_center_void_chain_second_backfill_applied"))
    right_center_chain_second_extra_alpha = number(
        layout.get("right_center_void_chain_second_backfill_extra_alpha_gain"), 0.0
    )
    right_center_chain_second_extra_void = number(
        layout.get("right_center_void_chain_second_backfill_extra_void_gain"), 0.0
    )
    if args.expect_right_center_chain_second_backfill == "off" and (
        right_center_chain_second_gate or right_center_chain_second_applied
    ):
        failures.append(
            "right_center_void_chain_second_backfill enabled/applied on a layout expected to keep it off"
        )
    if args.expect_right_center_chain_second_backfill == "on" and not right_center_chain_second_applied:
        failures.append("right_center_void_chain_second_backfill_applied is false")
    if (
        args.min_right_center_chain_second_extra_alpha_gain is not None
        and args.min_right_center_chain_second_extra_void_gain is not None
    ):
        if (
            right_center_chain_second_extra_alpha < args.min_right_center_chain_second_extra_alpha_gain
            and right_center_chain_second_extra_void < args.min_right_center_chain_second_extra_void_gain
        ):
            failures.append(
                "right_center_void_chain_second_backfill_extra gains "
                f"alpha={right_center_chain_second_extra_alpha:.4f} < {args.min_right_center_chain_second_extra_alpha_gain:.4f} "
                f"and void={right_center_chain_second_extra_void:.4f} < {args.min_right_center_chain_second_extra_void_gain:.4f}"
            )
    elif (
        args.min_right_center_chain_second_extra_alpha_gain is not None
        and right_center_chain_second_extra_alpha < args.min_right_center_chain_second_extra_alpha_gain
    ):
        failures.append(
            f"right_center_void_chain_second_backfill_extra_alpha_gain {right_center_chain_second_extra_alpha:.4f} < {args.min_right_center_chain_second_extra_alpha_gain:.4f}"
        )
    elif (
        args.min_right_center_chain_second_extra_void_gain is not None
        and right_center_chain_second_extra_void < args.min_right_center_chain_second_extra_void_gain
    ):
        failures.append(
            f"right_center_void_chain_second_backfill_extra_void_gain {right_center_chain_second_extra_void:.4f} < {args.min_right_center_chain_second_extra_void_gain:.4f}"
        )

    return {
        "label": args.label or Path(args.layout_json).name,
        "status": "FAIL" if failures else "PASS",
        "failures": failures,
        "version": layout.get("version"),
        "target_long_side_mm": layout.get("target_long_side_mm"),
        "seed": layout.get("seed"),
        "count": placement_count,
        "alpha": alpha,
        "bbox": bbox,
        "quality": quality,
        "orientation": orient,
        "right_center_void_relocate": right_center_gate,
        "right_center_void_relocate_applied": right_center_applied,
        "right_center_void_relocate_moves": integer(layout.get("right_center_void_relocate_moves"), 0),
        "right_center_void_relocate_gain": right_center_gain,
        "right_center_void_right_blank_before": layout.get("right_center_void_right_blank_before"),
        "right_center_void_right_blank_after": layout.get("right_center_void_right_blank_after"),
        "right_center_void_mid_right_blank_before": layout.get("right_center_void_mid_right_blank_before"),
        "right_center_void_mid_right_blank_after": layout.get("right_center_void_mid_right_blank_after"),
        "right_center_void_chain_relocate": right_center_chain_gate,
        "right_center_void_chain_relocate_applied": right_center_chain_applied,
        "right_center_void_chain_relocate_base_applied": right_center_chain_base_applied,
        "right_center_void_chain_relocate_ever_applied": right_center_chain_ever_applied,
        "right_center_void_chain_relocate_moves": integer(layout.get("right_center_void_chain_relocate_moves"), 0),
        "right_center_void_chain_relocate_alpha_gain": right_center_chain_alpha_gain,
        "right_center_void_chain_relocate_void_gain": right_center_chain_void_gain,
        "right_center_void_chain_relocate_ever_moves": integer(
            layout.get("right_center_void_chain_relocate_ever_moves"),
            integer(layout.get("right_center_void_chain_relocate_moves"), 0),
        ),
        "right_center_void_chain_relocate_ever_alpha_gain": right_center_chain_ever_alpha_gain,
        "right_center_void_chain_relocate_ever_void_gain": right_center_chain_ever_void_gain,
        "right_center_void_chain_second_backfill": right_center_chain_second_gate,
        "right_center_void_chain_second_backfill_applied": right_center_chain_second_applied,
        "right_center_void_chain_second_backfill_moves": integer(
            layout.get("right_center_void_chain_second_backfill_moves"), 0
        ),
        "right_center_void_chain_second_backfill_extra_alpha_gain": right_center_chain_second_extra_alpha,
        "right_center_void_chain_second_backfill_extra_void_gain": right_center_chain_second_extra_void,
        **replay,
    }


def print_text(summary):
    parts = [
        summary["status"],
        summary["label"],
        f"version={summary['version']}",
        f"target={summary['target_long_side_mm']}",
        f"seed={summary['seed']}",
        f"count={summary['count']}",
        f"alpha={summary['alpha']:.4f}",
        f"bbox={summary['bbox']:.4f}",
        f"quality={summary['quality']:.4f}",
        f"grid={summary['grid_w']}x{summary['grid_h']}",
        f"out_of_bounds={summary['out_of_bounds']}",
        f"overlap_cells={summary['overlap_cells']}",
        f"right_center_void_relocate={summary['right_center_void_relocate']}",
        f"right_center_void_relocate_applied={summary['right_center_void_relocate_applied']}",
        f"right_center_void_relocate_moves={summary['right_center_void_relocate_moves']}",
        f"right_center_void_relocate_gain={summary['right_center_void_relocate_gain']:.4f}",
        f"right_center_void_chain_relocate={summary['right_center_void_chain_relocate']}",
        f"right_center_void_chain_relocate_applied={summary['right_center_void_chain_relocate_applied']}",
        f"right_center_void_chain_relocate_ever_applied={summary['right_center_void_chain_relocate_ever_applied']}",
        f"right_center_void_chain_relocate_ever_moves={summary['right_center_void_chain_relocate_ever_moves']}",
        f"right_center_void_chain_relocate_ever_alpha_gain={summary['right_center_void_chain_relocate_ever_alpha_gain']:.4f}",
        f"right_center_void_chain_relocate_ever_void_gain={summary['right_center_void_chain_relocate_ever_void_gain']:.4f}",
        f"right_center_void_chain_second_backfill={summary['right_center_void_chain_second_backfill']}",
        f"right_center_void_chain_second_backfill_applied={summary['right_center_void_chain_second_backfill_applied']}",
        f"right_center_void_chain_second_backfill_moves={summary['right_center_void_chain_second_backfill_moves']}",
        f"right_center_void_chain_second_backfill_extra_alpha_gain={summary['right_center_void_chain_second_backfill_extra_alpha_gain']:.4f}",
        f"right_center_void_chain_second_backfill_extra_void_gain={summary['right_center_void_chain_second_backfill_extra_void_gain']:.4f}",
    ]
    orient = summary["orientation"]
    parts.append(
        "orientation="
        + ",".join(f"{key}={orient[key]}" for key in ("readable", "upright", "small", "upside", "sideways", "hard"))
    )
    print(" ".join(parts))
    if summary["overlap_pairs"]:
        print("overlap_pairs=" + json.dumps(summary["overlap_pairs"], ensure_ascii=False, sort_keys=True))
    for failure in summary["failures"]:
        print("failure: " + failure)


def parse_args():
    parser = argparse.ArgumentParser(description="Fast safety probe for StickerNest layout JSON files.")
    parser.add_argument("layout_json")
    parser.add_argument("--label", default="")
    parser.add_argument("--min-count", type=int, default=None)
    parser.add_argument("--min-alpha", type=float, default=None)
    parser.add_argument("--min-bbox", type=float, default=None)
    parser.add_argument("--max-bbox", type=float, default=None)
    parser.add_argument("--max-overlap-cells", type=int, default=0)
    parser.add_argument("--max-out-of-bounds", type=int, default=0)
    parser.add_argument("--strict-readable", action="store_true")
    parser.add_argument("--max-upside", type=int, default=None)
    parser.add_argument("--max-sideways", type=int, default=None)
    parser.add_argument("--max-hard", type=int, default=None)
    parser.add_argument("--expect-right-center", choices=("any", "off", "on"), default="any")
    parser.add_argument("--min-right-center-gain", type=float, default=None)
    parser.add_argument("--expect-right-center-chain", choices=("any", "off", "on"), default="any")
    parser.add_argument("--min-right-center-chain-alpha-gain", type=float, default=None)
    parser.add_argument("--min-right-center-chain-void-gain", type=float, default=None)
    parser.add_argument("--expect-right-center-chain-second-backfill", choices=("any", "off", "on"), default="any")
    parser.add_argument("--min-right-center-chain-second-extra-alpha-gain", type=float, default=None)
    parser.add_argument("--min-right-center-chain-second-extra-void-gain", type=float, default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    layout = json.loads(Path(args.layout_json).read_text())
    summary = evaluate(layout, args)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        print_text(summary)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
