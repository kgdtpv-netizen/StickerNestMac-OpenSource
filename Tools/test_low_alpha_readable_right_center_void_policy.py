#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
PYTHON = ROOT / "Tools" / "auto_nest.py"
BUILD = ROOT / "build.zsh"


def main() -> int:
    swift = SWIFT.read_text()
    python = PYTHON.read_text()
    build = BUILD.read_text()

    swift_markers = {
        'static let version = "1.1.244"': "AppInfo version should be bumped",
        'static let build = "20260607.005"': "AppInfo build should be bumped",
        'marketing_version="1.1.244"': "build.zsh marketing version should be bumped",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE": "Swift external right/center void env gate",
        "lowAlphaReadableRightCenterVoidRelocateEnabled": "Swift right/center enabled flag",
        "lowAlphaReadableRightCenterVoidRelocateMinVoidGain": "Swift right/center min void gain",
        "lowAlphaReadableRightCenterVoidRelocateNodeLimit": "Swift right/center node limit",
        "STICKERNEST_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE": "Swift should pass Python right/center gate",
        'environment["STICKERNEST_RIGHT_CENTER_VOID_RELOCATE_MIN_VOID_GAIN"]': "Swift should pass right/center min gain",
        'environment["STICKERNEST_RIGHT_CENTER_VOID_RELOCATE_NODE_LIMIT"]': "Swift should pass right/center node limit",
        'rightCenterVoid=\\(lowAlphaReadable && lowAlphaReadableRightCenterVoidRelocateEnabled)': "selected topup log should expose right/center gate",
        "rightCenterVoidMinGain=": "selected topup log should expose right/center min gain",
        "rightCenterVoidNodeLimit=": "selected topup log should expose right/center node limit",
        "version_low_alpha_readable_right_center_void_relocate_changed": "right/center cache invalidation key",
    }
    missing_swift = [
        label
        for marker, label in swift_markers.items()
        if marker not in swift and marker not in build
    ]
    if missing_swift:
        print("missing Swift right/center void markers: " + ", ".join(missing_swift))
        return 1

    env_pos = swift.find("STICKERNEST_SELECTED_MATERIAL_TOPUP_RUN")
    run_pos = swift.find("try process.run()", env_pos)
    if min(env_pos, run_pos) < 0:
        print("missing Swift selected topup env block")
        return 1
    env_block = swift[env_pos:run_pos]
    if 'environment["STICKERNEST_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE"] = lowAlphaReadable ? (lowAlphaReadableRightCenterVoidRelocateEnabled ? "1" : "0") : "0"' not in env_block:
        print("right/center void must only be enabled for low-alpha selected postprocess")
        return 1
    if 'environment["STICKERNEST_LOCAL_ADAPTER"] = "0"' not in env_block:
        print("right/center path must not enable local adapter")
        return 1

    cache_pos = swift.find("version_low_alpha_readable_right_center_void_relocate_changed")
    prior_pos = swift.find("version_low_alpha_readable_iterative_polish_changed")
    if min(cache_pos, prior_pos) < 0 or not (cache_pos < prior_pos):
        print("right/center cache invalidation should run before the previous low-alpha polish cache key")
        return 1

    python_markers = {
        "LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE": "Python right/center env flag",
        "STICKERNEST_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_RELOCATE": "Python right/center env key",
        "RIGHT_CENTER_VOID_RELOCATE_APPLIED": "Python right/center applied flag",
        "RIGHT_CENTER_VOID_RELOCATE_MOVES": "Python right/center move count",
        "RIGHT_CENTER_VOID_RELOCATE_GAIN": "Python right/center gain",
        "RIGHT_CENTER_VOID_RIGHT_BLANK_BEFORE": "Python right blank before metric",
        "RIGHT_CENTER_VOID_RIGHT_BLANK_AFTER": "Python right blank after metric",
        "RIGHT_CENTER_VOID_MID_RIGHT_BLANK_BEFORE": "Python mid-right blank before metric",
        "RIGHT_CENTER_VOID_MID_RIGHT_BLANK_AFTER": "Python mid-right blank after metric",
        "def right_center_void_metrics": "Python right/center metric helper",
        "def right_center_void_targets": "Python right/center target helper",
        "def right_center_void_relocate": "Python right/center relocation pass",
        'base_stats["readable"]<N': "Python right/center base must be fully readable",
        'base_stats["upside"]>0': "Python right/center base must reject upside",
        'base_stats["sideways"]>0': "Python right/center base must reject sideways",
        'base_stats["hard"]>0': "Python right/center base must reject hard orientations",
        'trial_stats["readable"]<N': "Python right/center trial must stay fully readable",
        'trial_stats["upside"]>0': "Python right/center trial must reject upside",
        'trial_stats["sideways"]>0': "Python right/center trial must reject sideways",
        'trial_stats["hard"]>0': "Python right/center trial must reject hard orientations",
        "right_center_void_relocate accepted": "Python right/center accepted log",
        "right_center_void_relocate rejected": "Python right/center rejected log",
        "rightCenterVoid={RIGHT_CENTER_VOID_RELOCATE_APPLIED}": "selected-layout log should expose right/center result",
        '"right_center_void_relocate"': "JSON should record right/center gate",
        '"right_center_void_relocate_applied"': "JSON should record applied flag",
        '"right_center_void_relocate_moves"': "JSON should record move count",
        '"right_center_void_relocate_gain"': "JSON should record void gain",
        '"right_center_void_right_blank_before"': "JSON should record right blank before",
        '"right_center_void_right_blank_after"': "JSON should record right blank after",
        '"right_center_void_mid_right_blank_before"': "JSON should record mid-right blank before",
        '"right_center_void_mid_right_blank_after"': "JSON should record mid-right blank after",
    }
    missing_python = [label for marker, label in python_markers.items() if marker not in python]
    if missing_python:
        print("missing Python right/center void markers: " + ", ".join(missing_python))
        return 1

    use_pos = python.find("if POLISH_BASE_JSON:")
    normal_post_pos = python.find("if bestpl is not None and not POLISH_BASE_JSON", use_pos)
    if min(use_pos, normal_post_pos) < 0:
        print("missing selected-layout mode block")
        return 1
    use_block = python[use_pos:normal_post_pos]
    order = [
        "band_void_fill_pair_relocate(polish_candidate, rounds=1)",
        "right_center_void_relocate(polish_candidate, rounds=1)",
        "scale_transfer_repack(polish_candidate, rounds=1)",
    ]
    positions = [use_block.find(marker) for marker in order]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        print("right/center void should run after band pair fill and before scale transfer")
        return 1

    normal_selected_test = (ROOT / "Tools" / "test_selected_material_postprocess_policy.py").read_text()
    if 'environment["STICKERNEST_SCALE_TRANSFER"] = "0"' not in normal_selected_test:
        print("normal selected-postprocess test must continue guarding heavy repackers off")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
