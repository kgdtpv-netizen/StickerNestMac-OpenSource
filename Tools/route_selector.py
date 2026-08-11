#!/usr/bin/env python3
"""Automatic target/route selection for already-cutout transparent PNG layouts.

Given several candidate layout JSON files produced by different target sizes
and routes (e.g. 102mm strict-readable, 104mm broad-rotation, 105mm, ...), this
tool picks the one to ship using the repository's safety-first product rule:

  - first keep only candidates that are exact-mask safe (all pieces placed,
    no overlap, no out-of-bounds);
  - among those, prefer strict-readable layouts (no upside / sideways / hard,
    every piece readable) and choose the one that saves the most material
    (highest alpha);
  - only when no strict-readable candidate exists, fall back to the
    orientation-safe tier (readable>=min, upside/sideways/hard within the same
    budget the app uses for selection) and again take the highest alpha;
  - never select a denser route that needs many upside/sideways/hard pieces
    when a safe route exists.

This is a read-only selector. It does not change any layout; it only reuses the
existing exact-mask replay and orientation reading from
Tools/layout_regression_probe.py so the offline selection matches what the app's
regression probe already enforces.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_regression_probe import (  # noqa: E402
    integer,
    number,
    orientation_summary,
    replay_mask_runs,
)


def evaluate_candidate(path: Path, args) -> dict:
    layout = json.loads(path.read_text())
    placements = layout.get("placements") or []
    count = len(placements)
    count_field = layout.get("count")
    alpha = number(layout.get("alpha"), 0.0)
    bbox = number(layout.get("coverage_bbox"), 0.0)
    target = number(layout.get("target_long_side_mm"), 0.0)
    replay = replay_mask_runs(layout)
    orient = orientation_summary(layout)

    reasons = []
    if count < args.min_count:
        reasons.append(f"count {count} < min_count {args.min_count}")
    if count_field is not None and integer(count_field) != count:
        reasons.append(f"count_field {integer(count_field)} != placements {count}")
    if replay["overlap_cells"] > args.max_overlap_cells:
        reasons.append(f"overlap_cells {replay['overlap_cells']} > {args.max_overlap_cells}")
    if replay["out_of_bounds"] > args.max_out_of_bounds:
        reasons.append(f"out_of_bounds {replay['out_of_bounds']} > {args.max_out_of_bounds}")
    exact_safe = not reasons

    strict_readable = (
        exact_safe
        and orient["readable"] == count
        and orient["upside"] == 0
        and orient["sideways"] == 0
        and orient["hard"] == 0
    )
    near_strict = (
        exact_safe
        and not strict_readable
        and args.near_strict
        and orient["readable"] >= args.near_strict_min_readable
        and orient["upside"] <= args.near_strict_max_upside
        and orient["sideways"] <= args.near_strict_max_sideways
        and orient["hard"] <= args.near_strict_max_hard
    )
    orientation_safe = (
        exact_safe
        and orient["readable"] >= args.min_readable
        and orient["upside"] <= args.max_upside
        and orient["sideways"] <= args.max_sideways
        and orient["hard"] <= args.max_hard
    )

    if strict_readable:
        tier = "strict_readable"
    elif near_strict:
        tier = "near_strict"
        reasons.append(
            "near-strict (almost fully upright) "
            f"(upside={orient['upside']}, sideways={orient['sideways']}, hard={orient['hard']})"
        )
    elif orientation_safe:
        tier = "orientation_safe"
        reasons.append(
            "not strict-readable "
            f"(upside={orient['upside']}, sideways={orient['sideways']}, hard={orient['hard']})"
        )
    else:
        tier = "rejected"
        if exact_safe:
            reasons.append(
                "orientation outside safe budget "
                f"(readable={orient['readable']}<{args.min_readable} or "
                f"upside={orient['upside']}>{args.max_upside} or "
                f"sideways={orient['sideways']}>{args.max_sideways} or "
                f"hard={orient['hard']}>{args.max_hard})"
            )

    return {
        "path": str(path),
        "label": path.name,
        "tier": tier,
        "accepted": tier in ("strict_readable", "near_strict", "orientation_safe"),
        "alpha": alpha,
        "bbox": bbox,
        "target_long_side_mm": target,
        "count": count,
        "overlap_cells": replay["overlap_cells"],
        "out_of_bounds": replay["out_of_bounds"],
        "orientation": orient,
        "notes": reasons,
    }


# Higher alpha wins (most material saved); ties break on bbox then larger target.
def _rank_key(candidate: dict):
    return (
        candidate["alpha"],
        candidate["bbox"],
        candidate["target_long_side_mm"],
    )


def select(candidates: list, near_strict_alpha_budget: float = 0.035) -> dict:
    strict = [c for c in candidates if c["tier"] == "strict_readable"]
    near = [c for c in candidates if c["tier"] == "near_strict"]
    safe = [c for c in candidates if c["tier"] == "orientation_safe"]

    if strict:
        # Strict always wins, regardless of alpha; pick the most material-saving.
        selected = max(strict, key=_rank_key)
    elif near or safe:
        best_near = max(near, key=_rank_key) if near else None
        best_safe = max(safe, key=_rank_key) if safe else None
        if best_near and best_safe:
            # Prefer the near-strict (almost upright) layout unless the safe layout
            # saves more material than the near-strict alpha budget allows.
            if best_safe["alpha"] - best_near["alpha"] <= near_strict_alpha_budget:
                selected = best_near
            else:
                selected = best_safe
        else:
            selected = best_near or best_safe
    else:
        selected = None

    return {
        "selected": selected,
        "selected_tier": selected["tier"] if selected else None,
        "strict_readable_count": len(strict),
        "near_strict_count": len(near),
        "orientation_safe_count": len(safe),
        "near_strict_alpha_budget": near_strict_alpha_budget,
        "candidates": sorted(candidates, key=lambda c: (-_rank_key(c)[0], c["label"])),
    }


def print_text(report: dict) -> None:
    selected = report["selected"]
    if selected is None:
        print("SELECTED none — no exact-safe, orientation-acceptable candidate")
    else:
        orient = selected["orientation"]
        print(
            f"SELECTED {selected['label']} tier={selected['tier']} "
            f"alpha={selected['alpha']:.4f} bbox={selected['bbox']:.4f} "
            f"target={selected['target_long_side_mm']:.1f} "
            f"orientation=readable={orient['readable']},upside={orient['upside']},"
            f"sideways={orient['sideways']},hard={orient['hard']}"
        )
    print(
        f"pool: strict_readable={report['strict_readable_count']} "
        f"near_strict={report['near_strict_count']} "
        f"orientation_safe={report['orientation_safe_count']} "
        f"total={len(report['candidates'])}"
    )
    for c in report["candidates"]:
        marker = "*" if selected and c["path"] == selected["path"] else " "
        orient = c["orientation"]
        print(
            f" {marker} [{c['tier']:>16}] {c['label']} alpha={c['alpha']:.4f} "
            f"target={c['target_long_side_mm']:.1f} "
            f"upside={orient['upside']} sideways={orient['sideways']} hard={orient['hard']}"
            + ("" if not c["notes"] else "  -- " + "; ".join(c["notes"]))
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pick the best safe layout among multiple target/route candidates."
    )
    parser.add_argument("layout_json", nargs="+", help="candidate layout JSON files")
    parser.add_argument("--min-count", type=int, default=25)
    parser.add_argument("--max-overlap-cells", type=int, default=0)
    parser.add_argument("--max-out-of-bounds", type=int, default=0)
    # Orientation-safe fallback budget mirrors the Swift selection gate
    # externalOrientationSelectionOK (readable>=20, upside<=6, sideways<=1, hard<=5).
    parser.add_argument("--min-readable", type=int, default=20)
    parser.add_argument("--max-upside", type=int, default=6)
    parser.add_argument("--max-sideways", type=int, default=1)
    parser.add_argument("--max-hard", type=int, default=5)
    # Near-strict direction-rescue tier (mirrors the Swift v1.1.233 gate):
    # readable>=23, upside<=1, sideways<=1, hard<=2, preferred over plain tier1 safe
    # within an alpha-loss budget (default 3.5pp).
    parser.add_argument("--near-strict", dest="near_strict", action="store_true", default=True)
    parser.add_argument("--no-near-strict", dest="near_strict", action="store_false")
    parser.add_argument("--near-strict-min-readable", type=int, default=23)
    parser.add_argument("--near-strict-max-upside", type=int, default=1)
    parser.add_argument("--near-strict-max-sideways", type=int, default=1)
    parser.add_argument("--near-strict-max-hard", type=int, default=2)
    parser.add_argument("--near-strict-alpha-budget", type=float, default=0.035)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = [evaluate_candidate(Path(p), args) for p in args.layout_json]
    report = select(candidates, near_strict_alpha_budget=args.near_strict_alpha_budget)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["selected"] is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
