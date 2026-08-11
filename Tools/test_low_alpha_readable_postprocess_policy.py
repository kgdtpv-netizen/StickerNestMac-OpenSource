#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
PYTHON = ROOT / "Tools" / "auto_nest.py"


def main() -> int:
    swift = SWIFT.read_text()
    python = PYTHON.read_text()

    swift_markers = {
        'static let version = "1.1.244"': "AppInfo version should be bumped",
        'static let build = "20260607.005"': "AppInfo build should be bumped",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_POSTPROCESS": "low-alpha readable env gate",
        "lowAlphaReadablePostprocessEnabled": "low-alpha readable enabled flag",
        "lowAlphaReadableMinAlpha": "low-alpha readable minimum alpha",
        "?? 0.435": "low-alpha readable floor should include Ochoa 44.8% candidates",
        "lowAlphaReadableSelectedMaterialTopupTargetGain": "low-alpha readable selected target gain",
        "lowAlphaReadableSelectedMaterialTopupMaxDeficit": "low-alpha readable selected max deficit",
        "lowAlphaReadableSelectedMaterialTopupMaxMoves": "low-alpha readable selected material move budget",
        "lowAlphaReadableSelectedMaterialTopupMaxNudge": "low-alpha readable selected material nudge budget",
        "lowAlphaReadableSelectedMaterialTopupSeconds": "low-alpha readable selected seconds budget",
        "lowAlphaReadableMultiPieceTopupMaxMoves": "low-alpha readable multi-piece move budget",
        "lowAlphaReadableMultiPieceTopupMaxNudge": "low-alpha readable multi-piece nudge budget",
        "lowAlphaReadableMultiPieceTopupNodeLimit": "low-alpha readable multi-piece node budget",
        "lowAlphaReadableMultiPieceTopupTargets": "low-alpha readable multi-piece target budget",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_STRUCTURAL_MICRO_GROW": "low-alpha selected structural micro-grow env gate",
        "lowAlphaReadableStructuralMicroGrowEnabled": "low-alpha selected structural micro-grow enabled flag",
        "lowAlphaReadableStructuralMicroGrowMinAcceptGain": "low-alpha selected structural micro-grow min accept gain",
        "lowAlphaReadableStructuralMicroGrowNodeLimit": "low-alpha selected structural micro-grow node limit",
        "lowAlphaReadableStructuralMicroGrowMaxBlockers": "low-alpha selected structural micro-grow blocker cap",
        "lowAlphaReadableStructuralMicroGrowOptions": "low-alpha selected structural micro-grow option cap",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK": "low-alpha selected structural blocker-shrink env gate",
        "lowAlphaReadableStructuralMicroGrowBlockerShrinkEnabled": "low-alpha selected structural blocker-shrink enabled flag",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_SMALL_GROUP_MATERIAL_REPACK": "low-alpha selected small-group env gate",
        "lowAlphaReadableSmallGroupMaterialRepackEnabled": "low-alpha selected small-group enabled flag",
        "lowAlphaReadableSmallGroupMaterialRepackMinAcceptGain": "low-alpha selected small-group min accept gain",
        "lowAlphaReadableSmallGroupMaterialRepackNodeLimit": "low-alpha selected small-group node limit",
        "lowAlphaReadableSmallGroupMaterialRepackTargets": "low-alpha selected small-group target limit",
        "lowAlphaReadableSmallGroupMaterialRepackNear": "low-alpha selected small-group near limit",
        "lowAlphaReadableSmallGroupMaterialRepackOptions": "low-alpha selected small-group option limit",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_BAND_VOID_FILL": "low-alpha selected band-void-fill env gate",
        "lowAlphaReadableBandVoidFillEnabled": "low-alpha selected band-void-fill enabled flag",
        "lowAlphaReadableBandVoidFillMinAcceptGain": "low-alpha selected band-void-fill min accept gain",
        "lowAlphaReadableBandVoidFillNodeLimit": "low-alpha selected band-void-fill node limit",
        "lowAlphaReadableBandVoidFillTargets": "low-alpha selected band-void-fill target limit",
        "lowAlphaReadableBandVoidFillDonors": "low-alpha selected band-void-fill donor limit",
        "lowAlphaReadableBandVoidFillOptions": "low-alpha selected band-void-fill option limit",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR": "low-alpha selected band-void-fill pair env gate",
        "lowAlphaReadableBandVoidFillPairEnabled": "low-alpha selected band-void-fill pair enabled flag",
        "lowAlphaReadableBandVoidFillPairMinVoidGain": "low-alpha selected band-void-fill pair min void gain",
        "lowAlphaReadableBandVoidFillPairNodeLimit": "low-alpha selected band-void-fill pair node limit",
        "lowAlphaReadableBandVoidFillPairBackfills": "low-alpha selected band-void-fill pair backfill limit",
        "lowAlphaReadableCandidate": "saved low-alpha readable candidate",
        "lowAlphaReadableCandidate = candidate": "candidate saved before alpha rejection",
        "external_auto_nest_low_alpha_readable_candidate": "audit log for saved candidate",
        "selectedMaterialTopupCandidate(from: currentBest, lowAlphaReadable: false)": "normal selected postprocess stays explicit",
        "selectedMaterialTopupCandidate(from: lowAlphaReadableCandidate, lowAlphaReadable: true)": "low-alpha selected postprocess path",
        "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_SCALE_TRANSFER": "low-alpha scale transfer env gate",
        'environment["STICKERNEST_LOW_ALPHA_READABLE_STRUCTURAL_MICRO_GROW"] = lowAlphaReadable ? (lowAlphaReadableStructuralMicroGrowEnabled ? "1" : "0") : "0"': "low-alpha path should pass structural micro-grow gate",
        'environment["STICKERNEST_STRUCTURAL_MICRO_GROW"] = lowAlphaReadableStructuralMicroGrowEnabled ? "1" : "0"': "low-alpha path may enable structural micro-grow",
        'environment["STICKERNEST_STRUCTURAL_MICRO_GROW_MIN_ACCEPT"] = String(format: "%.4f", lowAlphaReadableStructuralMicroGrowMinAccept)': "low-alpha path should pass structural micro-grow min accept",
        'environment["STICKERNEST_STRUCTURAL_MICRO_GROW_NODE_LIMIT"] = "\\(lowAlphaReadableStructuralMicroGrowNodeLimit)"': "low-alpha path should pass structural micro-grow node cap",
        'environment["STICKERNEST_STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK"] = lowAlphaReadableStructuralMicroGrowBlockerShrinkEnabled ? "1" : "0"': "low-alpha path should pass structural blocker-shrink gate",
        'environment["STICKERNEST_SCALE_TRANSFER"] = lowAlphaReadableScaleTransferEnabled ? "1" : "0"': "low-alpha path may enable scale transfer",
        'environment["STICKERNEST_SMALL_GROUP_MATERIAL_REPACK"] = lowAlphaReadableSmallGroupMaterialRepackEnabled ? "1" : "0"': "low-alpha path may enable selected-only small-group repack",
        'environment["STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_MIN_ACCEPT"] = String(format: "%.4f", lowAlphaReadableSmallGroupMaterialRepackMinAccept)': "low-alpha path should pass small-group min accept",
        'environment["STICKERNEST_LOW_ALPHA_READABLE_BAND_VOID_FILL"] = lowAlphaReadable ? (lowAlphaReadableBandVoidFillEnabled ? "1" : "0") : "0"': "low-alpha path should pass band-void-fill gate",
        'environment["STICKERNEST_BAND_VOID_FILL_MIN_ACCEPT"] = String(format: "%.4f", lowAlphaReadableBandVoidFillMinAccept)': "low-alpha path should pass band-void-fill min accept",
        'environment["STICKERNEST_LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR"] = lowAlphaReadable ? (lowAlphaReadableBandVoidFillPairEnabled ? "1" : "0") : "0"': "low-alpha path should pass band-void-fill pair gate",
        'environment["STICKERNEST_BAND_VOID_FILL_PAIR_MIN_VOID_GAIN"] = String(format: "%.4f", lowAlphaReadableBandVoidFillPairMinVoidGain)': "low-alpha path should pass band-void-fill pair min void gain",
        'structuralMicroGrow=\\(lowAlphaReadable && lowAlphaReadableStructuralMicroGrowEnabled)': "selected topup log should expose structural micro-grow gate",
        'structuralBlockerShrink=\\(lowAlphaReadable && lowAlphaReadableStructuralMicroGrowBlockerShrinkEnabled)': "selected topup log should expose structural blocker-shrink gate",
        'smallGroupRepack=\\(lowAlphaReadable && lowAlphaReadableSmallGroupMaterialRepackEnabled)': "selected topup log should expose small-group gate",
        'bandVoidFill=\\(lowAlphaReadable && lowAlphaReadableBandVoidFillEnabled)': "selected topup log should expose band-void-fill gate",
        'bandVoidPair=\\(lowAlphaReadable && lowAlphaReadableBandVoidFillPairEnabled)': "selected topup log should expose band-void-fill pair gate",
        "version_low_alpha_readable_postprocess_changed": "cache invalidation key",
        "version_low_alpha_readable_selected_polish_changed": "selected polish cache invalidation key",
        "version_low_alpha_readable_structural_micro_grow_changed": "selected structural micro-grow cache invalidation key",
        "version_low_alpha_readable_structural_micro_grow_blocker_shrink_changed": "selected structural blocker-shrink cache invalidation key",
        "version_low_alpha_readable_small_group_repack_changed": "selected small-group cache invalidation key",
        "version_low_alpha_readable_band_void_fill_changed": "selected band-void-fill cache invalidation key",
        "version_low_alpha_readable_band_void_fill_pair_changed": "selected band-void-fill pair cache invalidation key",
        "version_low_alpha_readable_iterative_polish_changed": "selected iterative polish cache invalidation key",
        # v1.1.244 selected strict-readable low-alpha polish
        "selectedStrictReadableLowAlphaPolishGate": "selected strict-readable low-alpha polish gate helper",
        "allowStrictReadableLowAlphaPolish": "relax materialTopup guard for strict-readable low-alpha polish",
        "lowAlphaReadable: true, allowStrictReadableLowAlphaPolish: true": "strict-readable low-alpha polish runs the low-alpha path",
        "external_auto_nest_selected_strict_readable_low_alpha_polish_begin": "strict-readable low-alpha polish begin log",
        "external_auto_nest_selected_strict_readable_low_alpha_polish_accept": "strict-readable low-alpha polish accept log",
        "external_auto_nest_selected_strict_readable_low_alpha_polish_reject": "strict-readable low-alpha polish reject log",
        "version_selected_strict_readable_low_alpha_polish_changed": "selected strict-readable low-alpha polish cache invalidation key",
        # v1.1.244 selected strict-readable material polish
        "selectedStrictReadableMaterialPolishGate": "selected strict-readable material polish gate helper",
        "external_auto_nest_selected_strict_readable_material_polish_begin": "strict-readable material polish begin log",
        "external_auto_nest_selected_strict_readable_material_polish_accept": "strict-readable material polish accept log",
        "external_auto_nest_selected_strict_readable_material_polish_reject": "strict-readable material polish reject log",
        "version_selected_strict_readable_material_polish_changed": "selected strict-readable material polish cache invalidation key",
    }
    missing_swift = [label for marker, label in swift_markers.items() if marker not in swift]
    if missing_swift:
        print("missing Swift low-alpha-readable markers: " + ", ".join(missing_swift))
        return 1

    alpha_reject = swift.find("if alpha < acceptAlpha")
    save_candidate = swift.find("lowAlphaReadableCandidate = candidate")
    reject_log = swift.find("reason=alpha_below_floor")
    if min(alpha_reject, save_candidate, reject_log) < 0:
        print("missing alpha rejection or low-alpha save ordering markers")
        return 1
    if not (alpha_reject < save_candidate < reject_log):
        print("low-alpha readable candidate must be saved before alpha_below_floor continue")
        return 1

    strict_orientation_block = swift[alpha_reject:reject_log]
    strict_markers = {
        "orientationStats.readable == items.count": "must require all readable",
        "orientationStats.upside == 0": "must reject upside-down pieces",
        "orientationStats.sideways == 0": "must reject sideways pieces",
        "orientationStats.hard == 0": "must reject hard orientations",
        "alpha >= lowAlphaReadableMinAlpha": "must require minimum low alpha",
    }
    missing_strict = [label for marker, label in strict_markers.items() if marker not in strict_orientation_block]
    if missing_strict:
        print("missing strict low-alpha-readable guards: " + ", ".join(missing_strict))
        return 1

    python_markers = {
        "LOW_ALPHA_READABLE_POSTPROCESS": "Python low-alpha postprocess env",
        "STICKERNEST_LOW_ALPHA_READABLE_POSTPROCESS": "Python env key",
        "LOW_ALPHA_READABLE_SCALE_TRANSFER": "Python low-alpha scale-transfer env",
        "LOW_ALPHA_READABLE_STRUCTURAL_MICRO_GROW": "Python low-alpha structural micro-grow env",
        "STICKERNEST_LOW_ALPHA_READABLE_STRUCTURAL_MICRO_GROW": "Python low-alpha structural micro-grow env key",
        "STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK": "Python structural blocker-shrink env",
        "STICKERNEST_STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK": "Python structural blocker-shrink env key",
        "LOW_ALPHA_READABLE_SMALL_GROUP_MATERIAL_REPACK": "Python low-alpha small-group env",
        "STICKERNEST_LOW_ALPHA_READABLE_SMALL_GROUP_MATERIAL_REPACK": "Python low-alpha small-group env key",
        "LOW_ALPHA_READABLE_BAND_VOID_FILL": "Python low-alpha band-void-fill env",
        "STICKERNEST_LOW_ALPHA_READABLE_BAND_VOID_FILL": "Python low-alpha band-void-fill env key",
        "BAND_VOID_FILL_APPLIED": "Python band-void-fill applied flag",
        "band_void_fill_relocate": "Python band-void-fill relocation function",
        "LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR": "Python low-alpha band-void-fill pair env",
        "STICKERNEST_LOW_ALPHA_READABLE_BAND_VOID_FILL_PAIR": "Python low-alpha band-void-fill pair env key",
        "BAND_VOID_FILL_PAIR_APPLIED": "Python band-void-fill pair applied flag",
        "band_void_fill_pair_relocate": "Python band-void-fill pair relocation function",
        "scale_transfer_repack(polish_candidate, rounds=1)": "selected JSON may run scale transfer only under low-alpha gate",
        "structural_micro_grow(polish_candidate, rounds=1)": "selected JSON may run structural micro-grow only under low-alpha gate",
        "small_group_material_repack(polish_candidate, rounds=1)": "selected JSON may run small-group repack only under low-alpha gate",
        "band_void_fill_relocate(polish_candidate, rounds=1)": "selected JSON may run band-void-fill only under low-alpha gate",
        "band_void_fill_pair_relocate(polish_candidate, rounds=1)": "selected JSON may run pair band-void-fill only under low-alpha gate",
        "structuralMicroGrow={STRUCTURAL_MICRO_GROW_APPLIED}": "Python selected-layout log should expose structural micro-grow result",
        "structuralBlockerShrink={STRUCTURAL_MICRO_GROW_BLOCKER_SHRINK}": "Python selected-layout log should expose structural blocker-shrink gate",
        '"structural_micro_grow_blocker_shrink"': "JSON should record structural blocker-shrink gate",
        "bandVoidFill={BAND_VOID_FILL_APPLIED}": "Python selected-layout log should expose band-void-fill result",
        "bandVoidPair={BAND_VOID_FILL_PAIR_APPLIED}": "Python selected-layout log should expose band-void-fill pair result",
    }
    missing_python = [label for marker, label in python_markers.items() if marker not in python]
    if missing_python:
        print("missing Python low-alpha-readable markers: " + ", ".join(missing_python))
        return 1

    selected_test = (ROOT / "Tools" / "test_selected_material_postprocess_policy.py").read_text()
    if 'environment["STICKERNEST_SCALE_TRANSFER"] = "0"' not in selected_test:
        print("normal selected-postprocess test must continue guarding scale transfer off")
        return 1
    build = (ROOT / "build.zsh").read_text()
    if 'marketing_version="1.1.244"' not in build:
        print("build.zsh marketing version should be bumped to 1.1.244")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
