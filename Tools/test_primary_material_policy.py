#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required_markers = {
        "STICKERNEST_EXTERNAL_PRIMARY_VISUAL_LOOKAHEAD_SEEDS": "primary visual lookahead env",
        "STICKERNEST_EXTERNAL_PRIMARY_MATERIAL_PROTECT_ALPHA": "material alpha protection env",
        "external_auto_nest_primary_material_visual_lookahead": "lookahead log",
        "external_auto_nest_candidate_rejected_by_material_alpha_protection": "protected rejection log",
        "version_primary_material_visual_lookahead_changed": "cache invalidation key",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing policy markers: " + ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
