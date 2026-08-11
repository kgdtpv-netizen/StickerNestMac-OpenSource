#!/usr/bin/env python3
"""Red-first policy tests for Tools/route_selector.py.

The route selector must, given several candidate layout JSON files from
different target/route attempts:
  1. filter out candidates that are incomplete, overlap, or go out of bounds;
  2. prefer strict-readable (no upside/sideways/hard) exact-safe candidates;
  3. among the accepted tier, pick the highest alpha (most material saved);
  4. never select a high-alpha route that needs many upside/sideways/hard
     pieces when a safe route exists;
  5. fall back to the orientation-safe tier only when no strict-readable
     candidate exists, and report failure when nothing is safe.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECTOR = ROOT / "Tools" / "route_selector.py"


def write_layout(
    path: Path,
    *,
    count: int = 25,
    alpha: float = 0.50,
    bbox: float = 0.90,
    target: float = 105.0,
    seed: int = 4,
    overlap: bool = False,
    out_of_bounds: bool = False,
    readable=None,
    upside: int = 0,
    sideways: int = 0,
    hard: int = 0,
) -> None:
    if readable is None:
        readable = count
    placements = []
    for i in range(count):
        # Lay pieces on a wide non-overlapping row by default.
        mask_x = 0 if (overlap and i < 2) else i * 40
        runs = [{"y": 0, "x0": 0, "x1": 2}]
        if out_of_bounds and i == 0:
            runs = [{"y": 9999, "x0": 0, "x1": 2}]
        placements.append(
            {
                "name": f"img{i}.png",
                "mask_x": mask_x,
                "mask_y": 0,
                "mask_downsample": 20,
                "mask_runs": runs,
            }
        )
    layout = {
        "sheet_w_px": max(4000, count * 40 * 20 + 100),
        "sheet_h_px": 4000,
        "mask_downsample": 20,
        "alpha": alpha,
        "coverage_bbox": bbox,
        "quality_score": 2.5,
        "target_long_side_mm": target,
        "seed": seed,
        "count": count,
        "orientation_stats": {
            "readable": readable,
            "upright": max(0, readable - 0),
            "small": 0,
            "upside": upside,
            "sideways": sideways,
            "hard": hard,
        },
        "placements": placements,
    }
    path.write_text(json.dumps(layout))


def run_selector(*paths_and_args):
    result = subprocess.run(
        [sys.executable, str(SELECTOR), "--json", *[str(p) for p in paths_and_args]],
        capture_output=True,
        text=True,
    )
    return result


def parse_choice(result):
    assert result.returncode == 0, f"selector failed: {result.stderr or result.stdout}"
    return json.loads(result.stdout)


def test_strict_readable_beats_higher_alpha_broad_rotation(tmp: Path) -> None:
    # The real test4 reactive case: 104mm broad-rotation has higher alpha but
    # 6 upside / 1 sideways / 7 hard; 102mm strict readable is lower alpha but safe.
    broad = tmp / "t4_104_broad.json"
    strict = tmp / "t4_102_strict.json"
    write_layout(broad, target=104.0, alpha=0.5350, readable=11, upside=6, sideways=1, hard=7)
    write_layout(strict, target=102.0, alpha=0.5190, readable=25)
    choice = parse_choice(run_selector(broad, strict))
    assert choice["selected"] is not None
    assert Path(choice["selected"]["path"]).name == "t4_102_strict.json", choice
    assert choice["selected"]["tier"] == "strict_readable", choice


def test_max_alpha_within_strict_tier(tmp: Path) -> None:
    low = tmp / "s_low.json"
    high = tmp / "s_high.json"
    write_layout(low, target=102.0, alpha=0.5190)
    write_layout(high, target=105.0, alpha=0.5784)
    choice = parse_choice(run_selector(low, high))
    assert Path(choice["selected"]["path"]).name == "s_high.json", choice


def test_overlap_and_oob_filtered(tmp: Path) -> None:
    bad_overlap = tmp / "bad_overlap.json"
    bad_oob = tmp / "bad_oob.json"
    good = tmp / "good.json"
    write_layout(bad_overlap, alpha=0.60, overlap=True)
    write_layout(bad_oob, alpha=0.59, out_of_bounds=True)
    write_layout(good, alpha=0.50)
    choice = parse_choice(run_selector(bad_overlap, bad_oob, good))
    assert Path(choice["selected"]["path"]).name == "good.json", choice
    rejected = {Path(c["path"]).name: c for c in choice["candidates"] if not c["accepted"]}
    assert "bad_overlap.json" in rejected
    assert "bad_oob.json" in rejected


def test_incomplete_count_filtered(tmp: Path) -> None:
    incomplete = tmp / "incomplete.json"
    good = tmp / "good.json"
    write_layout(incomplete, count=24, alpha=0.60)
    write_layout(good, count=25, alpha=0.50)
    choice = parse_choice(run_selector(incomplete, good))
    assert Path(choice["selected"]["path"]).name == "good.json", choice


def test_fallback_to_orientation_safe_when_no_strict(tmp: Path) -> None:
    # No strict-readable and no near-strict candidate; both are plain orientation-safe
    # (readable < 23 or > 1 upside), so the higher-alpha one wins.
    a = tmp / "safe_a.json"
    b = tmp / "safe_b.json"
    write_layout(a, alpha=0.52, readable=22, upside=3, sideways=0, hard=3)
    write_layout(b, alpha=0.55, readable=21, upside=4, sideways=0, hard=4)
    choice = parse_choice(run_selector(a, b))
    assert choice["selected"]["tier"] == "orientation_safe", choice
    assert Path(choice["selected"]["path"]).name == "safe_b.json", choice


def test_near_strict_beats_denser_safe_within_budget(tmp: Path) -> None:
    # The real test3 case: 113.3 seed4 is tier1 safe (alpha 55.5%, readable=20, upside=5,
    # hard=5); 111.0 seed400 is near-strict (alpha 52.3%, readable=23, upside=1, sideways=1,
    # hard=2). Alpha loss 3.2pp <= 3.5pp budget, so the near-strict route should win.
    safe = tmp / "t3_1133_safe.json"
    near = tmp / "t3_1110_near.json"
    write_layout(safe, target=113.3, alpha=0.555, readable=20, upside=5, sideways=0, hard=5)
    write_layout(near, target=111.0, alpha=0.523, readable=23, upside=1, sideways=1, hard=2)
    choice = parse_choice(run_selector(safe, near))
    assert choice["selected"]["tier"] == "near_strict", choice
    assert Path(choice["selected"]["path"]).name == "t3_1110_near.json", choice


def test_material_first_when_near_strict_exceeds_budget(tmp: Path) -> None:
    # If the safe route saves much more material than the budget allows, keep it.
    safe = tmp / "dense_safe.json"
    near = tmp / "low_near.json"
    write_layout(safe, target=113.3, alpha=0.580, readable=20, upside=5, sideways=0, hard=5)
    write_layout(near, target=105.0, alpha=0.500, readable=23, upside=1, sideways=1, hard=2)
    choice = parse_choice(run_selector(safe, near))
    assert choice["selected"]["tier"] == "orientation_safe", choice
    assert Path(choice["selected"]["path"]).name == "dense_safe.json", choice


def test_strict_beats_near_strict(tmp: Path) -> None:
    # A fully upright strict route wins even if a near-strict route saves more material.
    strict = tmp / "strict.json"
    near = tmp / "near.json"
    write_layout(strict, target=102.0, alpha=0.515, readable=25)
    write_layout(near, target=111.0, alpha=0.560, readable=23, upside=1, sideways=1, hard=2)
    choice = parse_choice(run_selector(strict, near))
    assert choice["selected"]["tier"] == "strict_readable", choice
    assert Path(choice["selected"]["path"]).name == "strict.json", choice


def test_no_safe_candidate_fails(tmp: Path) -> None:
    only_bad = tmp / "only_bad.json"
    write_layout(only_bad, alpha=0.60, readable=10, upside=9, sideways=4, hard=8)
    result = run_selector(only_bad)
    assert result.returncode != 0, result.stdout


def main() -> int:
    tests = [
        test_strict_readable_beats_higher_alpha_broad_rotation,
        test_max_alpha_within_strict_tier,
        test_overlap_and_oob_filtered,
        test_incomplete_count_filtered,
        test_fallback_to_orientation_safe_when_no_strict,
        test_near_strict_beats_denser_safe_within_budget,
        test_material_first_when_near_strict_exceeds_budget,
        test_strict_beats_near_strict,
        test_no_safe_candidate_fails,
    ]
    failures = 0
    for test in tests:
        with tempfile.TemporaryDirectory() as raw:
            try:
                test(Path(raw))
                print(f"PASS {test.__name__}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
