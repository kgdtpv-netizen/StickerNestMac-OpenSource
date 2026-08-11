#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required_markers = {
        "STICKERNEST_EXTERNAL_ORIENTATION_SAFE_SELECTION": "orientation-safe selection env gate",
        "orientationSafeSelectionEnabled": "orientation-safe selection enabled flag",
        "STICKERNEST_EXTERNAL_ORIENTATION_SAFE_ALPHA_LOSS": "orientation-safe alpha-loss env",
        "orientationSafeAlphaLoss": "orientation-safe alpha-loss threshold",
        "externalOrientationSelectionOK": "shared selected-orientation OK helper",
        "orientationSelectionOK": "candidate stores selected-orientation state",
        "external_auto_nest_candidate_rejected_by_orientation_safe_selection": "unsafe candidate rejection log",
        "external_auto_nest_candidate_best_orientation_safe_upgrade": "safe candidate upgrade log",
        "version_orientation_safe_selection_changed": "cache invalidation key",
        "version_orientation_safe_upgrade_protection_changed": "orientation-safe upgrade protection cache invalidation key",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing orientation-safe selection markers: " + ", ".join(missing))
        return 1

    if "candidate.orientationSelectionOK" not in source or "bestCandidate?.orientationSelectionOK" not in source:
        print("candidate selection must compare current and candidate orientation safety")
        return 1

    if "bestCandidate.alpha - candidate.alpha <= orientationSafeAlphaLoss" not in source:
        print("safe orientation candidate should be able to replace unsafe best within alpha-loss budget")
        return 1

    if "candidate.alpha - bestCandidate.alpha <= orientationSafeAlphaLoss" not in source:
        print("unsafe orientation candidate should not replace safe best for only a small alpha gain")
        return 1

    if "candidate.alpha < primaryMaterialProtectAlpha && !isOrientationSafeUpgrade" not in source:
        print("orientation-safe upgrade should bypass material alpha protection within the alpha-loss budget")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
