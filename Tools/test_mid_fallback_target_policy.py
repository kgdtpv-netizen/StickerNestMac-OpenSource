#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required_markers = {
        "104.0": "104mm middle fallback target",
        "version_mid_fallback_target_changed": "cache invalidation key",
        "version_orientation_safe_upgrade_protection_changed": "previous cache key should remain",
        "appendAttemptSeed(seedIndex: 4, seed: 4, reusedPrimarySeed: true)": "104mm target can reuse proven seed4 first",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing middle fallback target policy markers: " + ", ".join(missing))
        return 1

    target_pos = source.find("[105.0, 104.0, 102.0]")
    reuse_pos = source.find("appendAttemptSeed(seedIndex: 4, seed: 4, reusedPrimarySeed: true)")
    if min(target_pos, reuse_pos) < 0:
        print("missing target-order or seed-reuse markers")
        return 1

    add_rescue_pos = source.find("addTarget(highReadableRescueTargetMM)")
    if add_rescue_pos >= 0 and add_rescue_pos > target_pos:
        print("high readable rescue target should run before 105/104/102 lower fallbacks")
        return 1

    cache_pos = source.find("version_mid_fallback_target_changed")
    previous_cache_pos = source.find("version_orientation_safe_upgrade_protection_changed")
    if min(cache_pos, previous_cache_pos) < 0 or cache_pos < previous_cache_pos:
        print("mid fallback target cache invalidation should be newer than v1.1.204 cache key")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
