#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "Tools" / "layout_regression_probe.py"


def write_layout(
    path: Path,
    *,
    overlap: bool = False,
    hard: int = 0,
    right_center: bool = False,
    chain_current: bool = False,
    chain_ever: bool = False,
    second_backfill: bool = False,
    second_extra_alpha: float = 0.0,
    second_extra_void: float = 0.0,
) -> None:
    placements = [
        {
            "name": "a.png",
            "mask_x": 0,
            "mask_y": 0,
            "mask_downsample": 20,
            "mask_runs": [{"y": 0, "x0": 0, "x1": 2}],
        },
        {
            "name": "b.png",
            "mask_x": 0 if overlap else 40,
            "mask_y": 0,
            "mask_downsample": 20,
            "mask_runs": [{"y": 0, "x0": 0, "x1": 2}],
        },
    ]
    path.write_text(
        json.dumps(
            {
                "sheet_w_px": 200,
                "sheet_h_px": 200,
                "mask_downsample": 20,
                "alpha": 0.51,
                "coverage_bbox": 0.93,
                "quality_score": 2.5,
                "count": 2,
                "right_center_void_relocate": right_center,
                "right_center_void_relocate_applied": right_center,
                "right_center_void_relocate_moves": 1 if right_center else 0,
                "right_center_void_relocate_gain": 0.01 if right_center else 0.0,
                "right_center_void_chain_relocate": chain_current or chain_ever,
                "right_center_void_chain_relocate_applied": chain_current,
                "right_center_void_chain_relocate_base_applied": chain_ever and not chain_current,
                "right_center_void_chain_relocate_ever_applied": chain_current or chain_ever,
                "right_center_void_chain_relocate_moves": 1 if chain_current else 0,
                "right_center_void_chain_relocate_alpha_gain": 0.0003 if chain_current else 0.0,
                "right_center_void_chain_relocate_void_gain": 0.006 if chain_current else 0.0,
                "right_center_void_chain_relocate_ever_moves": 2 if chain_ever else (1 if chain_current else 0),
                "right_center_void_chain_relocate_ever_alpha_gain": 0.0006 if chain_ever else (0.0003 if chain_current else 0.0),
                "right_center_void_chain_relocate_ever_void_gain": 0.0139 if chain_ever else (0.006 if chain_current else 0.0),
                "right_center_void_chain_second_backfill": second_backfill,
                "right_center_void_chain_second_backfill_applied": second_backfill,
                "right_center_void_chain_second_backfill_moves": 3 if second_backfill else 0,
                "right_center_void_chain_second_backfill_extra_alpha_gain": second_extra_alpha,
                "right_center_void_chain_second_backfill_extra_void_gain": second_extra_void,
                "target_long_side_mm": 105.0,
                "seed": 4,
                "orientation_stats": {
                    "readable": 2 - hard,
                    "upright": 2 - hard,
                    "small": 0,
                    "upside": 0,
                    "sideways": 0,
                    "hard": hard,
                },
                "placements": placements,
            },
            ensure_ascii=False,
        )
    )


def write_swift_clamp_layout(path: Path) -> None:
    # The second piece starts one 20px row below the first piece, but Swift rebuild
    # clamps it upward by one 5px cell at the sheet bottom, creating a real collision.
    placements = [
        {
            "name": "a.png",
            "mask_x": 20,
            "mask_y": 20,
            "mask_w": 1,
            "mask_h": 1,
            "mask_downsample": 20,
            "mask_runs": [{"y": 0, "x0": 0, "x1": 1}],
        },
        {
            "name": "b.png",
            "mask_x": 100,
            "mask_y": 40,
            "mask_w": 1,
            "mask_h": 1,
            "mask_downsample": 20,
            "mask_runs": [{"y": 0, "x0": 0, "x1": 1}],
        },
    ]
    path.write_text(
        json.dumps(
            {
                "sheet_w_px": 200,
                "sheet_h_px": 55,
                "mask_downsample": 20,
                "gap_model": "swift_square",
                "alpha": 0.51,
                "coverage_bbox": 0.93,
                "quality_score": 2.5,
                "count": 2,
                "target_long_side_mm": 105.0,
                "seed": 4,
                "orientation_stats": {
                    "readable": 2,
                    "upright": 2,
                    "small": 0,
                    "upside": 0,
                    "sideways": 0,
                    "hard": 0,
                },
                "placements": placements,
            },
            ensure_ascii=False,
        )
    )


def run_probe(layout: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(PROBE),
            str(layout),
            "--min-count",
            "2",
            "--min-alpha",
            "0.50",
            "--strict-readable",
            "--expect-right-center",
            "off",
            *extra,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def main() -> int:
    if not PROBE.exists():
        print("missing layout regression probe tool")
        return 1

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        ok = tmp / "ok.json"
        write_layout(ok)
        ok_result = run_probe(ok)
        if ok_result.returncode != 0 or "PASS" not in ok_result.stdout:
            print("expected clean layout to pass")
            print(ok_result.stdout)
            return 1

        overlap = tmp / "overlap.json"
        write_layout(overlap, overlap=True)
        overlap_result = run_probe(overlap)
        if overlap_result.returncode == 0 or "overlap_cells" not in overlap_result.stdout:
            print("expected overlap layout to fail with overlap_cells")
            print(overlap_result.stdout)
            return 1

        swift_clamp = tmp / "swift-clamp.json"
        write_swift_clamp_layout(swift_clamp)
        swift_clamp_result = run_probe(swift_clamp)
        if swift_clamp_result.returncode == 0 or "overlap_cells" not in swift_clamp_result.stdout:
            print("expected Swift-clamped bottom layout to fail with overlap_cells")
            print(swift_clamp_result.stdout)
            return 1

        hard = tmp / "hard.json"
        write_layout(hard, hard=1)
        hard_result = run_probe(hard)
        if hard_result.returncode == 0 or "hard" not in hard_result.stdout:
            print("expected hard orientation layout to fail")
            print(hard_result.stdout)
            return 1

        right_center = tmp / "right-center.json"
        write_layout(right_center, right_center=True)
        right_result = run_probe(right_center)
        if right_result.returncode == 0 or "right_center_void_relocate" not in right_result.stdout:
            print("expected normal-path right-center layout to fail")
            print(right_result.stdout)
            return 1

        right_ok_result = run_probe(
            right_center,
            "--expect-right-center",
            "on",
            "--min-right-center-gain",
            "0.005",
        )
        if right_ok_result.returncode != 0 or "right_center_void_relocate_gain" not in right_ok_result.stdout:
            print("expected explicit right-center layout to pass with a gain threshold")
            print(right_ok_result.stdout)
            return 1

        chain_final = tmp / "chain-final.json"
        write_layout(chain_final, right_center=True, chain_ever=True)
        chain_result = run_probe(
            chain_final,
            "--expect-right-center",
            "on",
            "--expect-right-center-chain",
            "on",
            "--min-right-center-chain-alpha-gain",
            "0.0005",
            "--min-right-center-chain-void-gain",
            "0.0100",
        )
        if (
            chain_result.returncode != 0
            or "right_center_void_chain_relocate_ever_applied=True" not in chain_result.stdout
            or "right_center_void_chain_relocate_applied=False" not in chain_result.stdout
        ):
            print("expected final-pass inherited chain layout to pass via ever-applied metadata")
            print(chain_result.stdout)
            return 1

        chain_off_result = run_probe(
            chain_final,
            "--expect-right-center",
            "on",
            "--expect-right-center-chain",
            "off",
        )
        if chain_off_result.returncode == 0 or "right_center_void_chain_relocate" not in chain_off_result.stdout:
            print("expected chain layout to fail when chain is expected off")
            print(chain_off_result.stdout)
            return 1

        second_zero = tmp / "second-zero.json"
        write_layout(second_zero, right_center=True, chain_current=True, second_backfill=True)
        second_zero_result = run_probe(
            second_zero,
            "--expect-right-center",
            "on",
            "--expect-right-center-chain",
            "on",
            "--expect-right-center-chain-second-backfill",
            "on",
            "--min-right-center-chain-second-extra-alpha-gain",
            "0.0001",
            "--min-right-center-chain-second-extra-void-gain",
            "0.0005",
        )
        if second_zero_result.returncode == 0 or "right_center_void_chain_second_backfill_extra" not in second_zero_result.stdout:
            print("expected zero-extra second-backfill layout to fail")
            print(second_zero_result.stdout)
            return 1

        second_alpha = tmp / "second-alpha.json"
        write_layout(second_alpha, right_center=True, chain_current=True, second_backfill=True, second_extra_alpha=0.0002)
        second_alpha_result = run_probe(
            second_alpha,
            "--expect-right-center",
            "on",
            "--expect-right-center-chain",
            "on",
            "--expect-right-center-chain-second-backfill",
            "on",
            "--min-right-center-chain-second-extra-alpha-gain",
            "0.0001",
            "--min-right-center-chain-second-extra-void-gain",
            "0.0005",
        )
        if second_alpha_result.returncode != 0 or "right_center_void_chain_second_backfill_applied=True" not in second_alpha_result.stdout:
            print("expected second-backfill layout to pass when extra alpha gain is positive")
            print(second_alpha_result.stdout)
            return 1

        second_void = tmp / "second-void.json"
        write_layout(second_void, right_center=True, chain_current=True, second_backfill=True, second_extra_void=0.0007)
        second_void_result = run_probe(
            second_void,
            "--expect-right-center",
            "on",
            "--expect-right-center-chain",
            "on",
            "--expect-right-center-chain-second-backfill",
            "on",
            "--min-right-center-chain-second-extra-alpha-gain",
            "0.0001",
            "--min-right-center-chain-second-extra-void-gain",
            "0.0005",
        )
        if second_void_result.returncode != 0 or "right_center_void_chain_second_backfill_extra_void_gain=0.0007" not in second_void_result.stdout:
            print("expected second-backfill layout to pass when extra void gain is positive")
            print(second_void_result.stdout)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
