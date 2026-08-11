#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required_markers = {
        "stableLowerTargetSeedBase": "stable lower-target seed base helper",
        "version_lower_target_stable_seed_changed": "cache invalidation key",
        "external_auto_nest_stable_lower_target_seed_base": "stable seed-base log",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing stable lower-target seed policy markers: " + ", ".join(missing))
        return 1

    if "abs(targetLongSideMM - 102.0) < 0.05" not in source or "return 500" not in source:
        print("102mm fallback target should keep seed500 even when target list is shortened")
        return 1

    if "abs(targetLongSideMM - 105.0) < 0.05" not in source or "return 400" not in source:
        print("105mm fallback target should keep seed400 even when target list is shortened")
        return 1

    if "stableSeedBase + seedIndex" not in source:
        print("fallback target-number seeds should use the stable seed base, not only attemptIndex * 100")
        return 1

    if "seed: attemptIndex * 100 + seedIndex" in source:
        print("fallback seed append still derives directly from attemptIndex")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
