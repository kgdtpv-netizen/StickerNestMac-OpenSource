#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    auto_source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()
    required_auto_markers = {
        "STICKERNEST_MATERIAL_ALPHA_TOPUP": "material alpha top-up env",
        "material_alpha_topup": "material alpha top-up pass",
        "MATERIAL_ALPHA_TOPUP_TARGET": "alpha target guard",
        "MATERIAL_ALPHA_TOPUP_MIN_GAIN": "partial top-up minimum gain guard",
        "MATERIAL_ALPHA_TOPUP_MIN_ACCEPT": "partial top-up minimum accept guard",
        "material_alpha_topup_alpha": "top-up uses exported alpha metric",
        "visual_audit_like": "visual audit guard",
        "\"material_alpha_topup\"": "output json marker",
        "\"material_alpha_topup_partial\"": "partial top-up output marker",
    }
    required_swift_markers = {
        "STICKERNEST_EXTERNAL_PRIMARY_MATERIAL_TOPUP": "Swift primary material top-up env",
        "STICKERNEST_EXTERNAL_PRIMARY_MATERIAL_TOPUP_TARGET_ALPHA": "Swift primary material top-up target env",
        "primaryMaterialTopupTargetAlpha": "Swift targeted top-up alpha",
        "STICKERNEST_MATERIAL_ALPHA_TOPUP": "Swift passes Python top-up env",
        "STICKERNEST_MATERIAL_ALPHA_TOPUP_MIN_GAIN": "Swift passes Python minimum gain env",
        "STICKERNEST_MATERIAL_ALPHA_TOPUP_MIN_ACCEPT": "Swift passes Python minimum accept env",
        "primaryMaterialTopupMaxMoves": "Swift targeted top-up max moves",
        "primaryMaterialTopupMaxNudge": "Swift targeted top-up max nudge",
        "primaryMaterialTopupEnabled": "Swift targeted top-up gate",
        "version_material_alpha_topup_partial_changed": "cache invalidation key",
    }
    missing = [label for marker, label in required_auto_markers.items() if marker not in auto_source]
    missing += [label for marker, label in required_swift_markers.items() if marker not in swift_source]
    if missing:
        print("missing material alpha top-up markers: " + ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
