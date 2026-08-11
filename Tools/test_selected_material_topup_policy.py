#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
BUILD = ROOT / "build.zsh"


def require(markers: dict[str, str], source: str) -> list[str]:
    return [label for marker, label in markers.items() if marker not in source]


def main() -> int:
    swift = SWIFT.read_text()
    build = BUILD.read_text()

    missing = require(
        {
            'static let version = "1.1.244"': "AppInfo version should be bumped",
            'static let build = "20260607.005"': "AppInfo build should be bumped",
            "STICKERNEST_EXTERNAL_SELECTED_MATERIAL_TOPUP": "selected material topup env gate",
            "selectedMaterialTopupEnabled": "selected material topup enabled flag",
            "selectedMaterialTopupMinGain": "selected material topup minimum gain",
            "selectedMaterialTopupMaxMoves": "selected material topup move cap",
            "selectedMaterialTopupMaxNudge": "selected material topup nudge cap",
            "selectedMaterialTopupSeconds": "selected material topup short budget",
            "materialTopupForAttempt": "candidate should remember whether topup already ran",
            "external_auto_nest_selected_material_topup_begin": "selected topup begin log",
            "external_auto_nest_selected_material_topup_accepted": "selected topup accepted log",
            "external_auto_nest_selected_material_topup_rejected": "selected topup rejected log",
            "selectedMaterialTopupOrientationOK": "selected topup must keep orientation no worse",
            "selectedMaterialTopupStrictSafeAngleOK": "safe-angle candidate must stay fully readable",
            "version_selected_material_topup_changed": "cache invalidation key",
        },
        swift,
    )
    if 'marketing_version="1.1.244"' not in build:
        missing.append("build.zsh marketing version should be bumped")
    if missing:
        print("missing selected material topup markers: " + ", ".join(missing))
        return 1

    selected_pos = swift.find("external_auto_nest_candidate_pool_selected")
    topup_pos = swift.find("external_auto_nest_selected_material_topup_begin")
    if min(selected_pos, topup_pos) < 0:
        print("missing selected-candidate or selected-topup log")
        return 1
    if not (topup_pos < selected_pos):
        print("selected material topup must run before final candidate_pool_selected log")
        return 1

    guard_pos = swift.find("selectedMaterialTopupEnabled")
    begin_pos = swift.find("external_auto_nest_selected_material_topup_begin", guard_pos)
    if min(guard_pos, begin_pos) < 0:
        print("missing selected topup guard block")
        return 1
    guard_block = swift[guard_pos:begin_pos]
    for marker, label in {
        "manualStaggerExternalMode": "selected topup should stay on the 25-piece manual-stagger route",
        "primaryMaterialTopupEnabled": "selected topup should reuse material-topup safety controls",
        "!bestCandidate.materialTopupForAttempt": "selected topup should only rerun candidates that missed topup",
        "bestCandidate.result.unplaced.isEmpty": "selected topup should only polish complete layouts",
    }.items():
        if marker not in guard_block:
            print("missing selected topup guard: " + label)
            return 1

    env_pos = swift.find("STICKERNEST_SELECTED_MATERIAL_TOPUP_RUN")
    launch_pos = swift.find("try process.run()", env_pos)
    if min(env_pos, launch_pos) < 0:
        print("missing selected topup env or process run block")
        return 1
    env_block = swift[env_pos:launch_pos]
    for marker, label in {
        'environment["STICKERNEST_MATERIAL_ALPHA_TOPUP"] = "1"': "selected topup should enable material alpha topup",
        'environment["STICKERNEST_MULTI_PIECE_TOPUP"] = "1"': "selected topup should enable multi-piece topup",
        'environment["STICKERNEST_LOCAL_ADAPTER"] = "0"': "selected topup must not enable local adapter",
        'environment["STICKERNEST_SCALE_TRANSFER"] = "0"': "selected topup must not enable scale transfer",
        'environment["STICKERNEST_SMALL_GROUP_MATERIAL_REPACK"] = "0"': "selected topup must not enable small-group repack",
        'environment["STICKERNEST_MATERIAL_ALPHA_TOPUP_SEEDS"] = "\\(bestCandidate.seed)"': "selected topup should replay the selected seed",
        'environment["STICKERNEST_MEMORY_LIMIT_MB"] = String(format: "%.0f", externalProcessMemoryLimitMB)': "selected topup must inherit memory cap",
    }.items():
        if marker not in env_block:
            print("missing selected topup env guard: " + label)
            return 1

    orientation_pos = swift.find("let selectedMaterialTopupOrientationOK")
    accept_pos = swift.find("external_auto_nest_selected_material_topup_accepted", orientation_pos)
    if min(orientation_pos, accept_pos) < 0:
        print("missing selected topup orientation accept block")
        return 1
    orientation_block = swift[orientation_pos:accept_pos]
    for marker, label in {
        "polishedOrientationStats.readable >= bestCandidate.orientationStats.readable": "readable count must not regress",
        "polishedOrientationStats.upside <= bestCandidate.orientationStats.upside": "upside-down count must not regress",
        "polishedOrientationStats.sideways <= bestCandidate.orientationStats.sideways": "sideways count must not regress",
        "polishedOrientationStats.hard <= bestCandidate.orientationStats.hard": "hard-orientation count must not regress",
        "bestCandidate.safeAngleVariant ? selectedMaterialTopupStrictSafeAngleOK": "safe-angle candidate should keep strict full-readability",
        "polishedAlpha >= bestCandidate.alpha + selectedMaterialTopupMinGain": "selected topup must prove alpha gain",
        "polishedAudit.score >= bestCandidate.audit.score - selectedMaterialTopupMaxVisualLoss": "visual score must not materially regress",
    }.items():
        if marker not in orientation_block:
            print("missing selected topup orientation/quality guard: " + label)
            return 1

    cache_pos = swift.find("version_selected_material_topup_changed")
    high_target_cache_pos = swift.find("version_safe_angle_high_target_changed")
    if min(cache_pos, high_target_cache_pos) < 0:
        print("missing selected topup cache ordering markers")
        return 1
    if not (cache_pos < high_target_cache_pos):
        print("selected topup cache invalidation should run before v1.1.212 high-target invalidation")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
