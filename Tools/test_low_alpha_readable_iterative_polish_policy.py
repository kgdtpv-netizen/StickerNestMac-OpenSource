#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    swift = SWIFT.read_text()
    build = (ROOT / "build.zsh").read_text()

    markers = {
        'static let version = "1.1.244"': "AppInfo version should be bumped",
        'static let build = "20260607.005"': "AppInfo build should be bumped",
        'marketing_version="1.1.244"': "build.zsh marketing version should be bumped",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_ITERATIVE_SELECTED_POLISH": "iterative low-alpha env gate",
        "lowAlphaReadableIterativeSelectedPolishEnabled": "iterative low-alpha enabled flag",
        "lowAlphaReadableSelectedPolishPasses": "bounded low-alpha polish pass count",
        "polishPass": "candidate should carry selected-polish pass count",
        "nextPolishPass": "selected topup should create a new pass id",
        "passSuffix": "selected topup should write distinct pass output files",
        "external_auto_nest_selected_material_topup_iteration": "iteration audit log",
        "version_low_alpha_readable_iterative_polish_changed": "cache invalidation key",
    }
    missing = [label for marker, label in markers.items()
               if marker not in swift and marker not in build]
    if missing:
        print("missing iterative low-alpha polish markers: " + ", ".join(missing))
        return 1

    guard_pos = swift.find("selectedMaterialTopupGuardOK")
    allow_pos = swift.find("bestCandidate.polishPass > 0", guard_pos)
    if guard_pos < 0 or allow_pos < 0:
        print("selected topup guard should explicitly allow already-polished low-alpha candidates")
        return 1

    normal_call = "selectedMaterialTopupCandidate(from: currentBest, lowAlphaReadable: false)"
    iterative_block = swift.find("external_auto_nest_selected_material_topup_iteration")
    low_alpha_call = swift.find("selectedMaterialTopupCandidate(from: lowAlphaReadableCandidate, lowAlphaReadable: true)")
    if min(iterative_block, low_alpha_call) < 0:
        print("missing low-alpha iterative selected-polish call")
        return 1
    if normal_call not in swift[:iterative_block]:
        print("normal selected topup path should remain separate before low-alpha iteration")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
