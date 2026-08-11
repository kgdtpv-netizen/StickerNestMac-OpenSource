#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
BUILD = ROOT / "build.zsh"


def main() -> int:
    swift = SWIFT.read_text()
    build = BUILD.read_text()

    required = {
        'static let version = "1.1.244"': "AppInfo version should be bumped",
        'static let build = "20260607.005"': "AppInfo build should be bumped",
        'marketing_version="1.1.244"': "build.zsh marketing version should be bumped",
        "let materialSavingTarget: Bool": "external candidates should remember material-saving origin",
        "materialSavingTarget: isMaterialSavingTarget": "raw attempt candidates should carry material-saving origin",
        "materialSavingTarget: bestCandidate.materialSavingTarget": "selected-polish candidates should preserve material-saving origin",
        "materialSavingLowAlphaPolishShouldReplaceBest": "material-saving low-alpha replacement helper",
        "materialSavingLowAlphaCandidateShouldReplaceSaved(candidate, saved: materialSavingLowAlphaReadableCandidate)": "only material-saving saved candidates use the new replacement path",
        "external_auto_nest_material_saving_low_alpha_polish_begin": "material-saving low-alpha polish should be logged",
        "selectedMaterialTopupCandidate(from: materialSavingLowAlphaReadableCandidate, lowAlphaReadable: true, allowStrictReadableLowAlphaPolish: true)": "material-saving low-alpha polish must bypass the material-topup-attempt guard",
        "external_auto_nest_material_saving_low_alpha_polish_accept": "accepted material-saving low-alpha polish should be logged",
        "external_auto_nest_material_saving_low_alpha_polish_reject": "rejected material-saving low-alpha polish should be logged",
        "materialSavingLowAlphaCandidateShouldReplaceBest": "raw material-saving low-alpha fallback helper",
        "materialSavingLowAlphaStageStopShouldStop": "stage stop helper should allow the saved material-saving candidate to be the current best",
        "materialSavingStageStopCandidate": "stage stop should also consider the current material-saving best candidate",
        "materialSavingLowAlphaCandidateShouldReplaceSaved": "saved material-saving low-alpha helper should keep the best alpha candidate",
        "var materialSavingLowAlphaReadableCandidate: ExternalCandidate?": "material-saving low-alpha candidate must be tracked separately from generic low-alpha candidate",
        "materialSavingLowAlphaReadableCandidate = candidate": "material-saving low-alpha candidate should be saved separately",
        "external_auto_nest_material_saving_low_alpha_readable_candidate": "saved material-saving low-alpha candidate should be logged separately",
        "materialSavingLowAlphaReadableCandidate": "stage stop and material-saving polish should use the material-saving saved candidate",
        "external_auto_nest_material_saving_low_alpha_raw_accept": "raw material-saving low-alpha fallback accept log",
        "external_auto_nest_material_saving_low_alpha_raw_reject": "raw material-saving low-alpha fallback reject log",
        "external_auto_nest_material_saving_low_alpha_stop_before_normal_targets": "safe material-saving low-alpha candidate should stop before normal target ladder",
        "external_auto_nest_material_saving_low_alpha_stop_before_lower_targets": "safe material-saving low-alpha candidate should skip lower material-saving targets",
        "let nextTargetIsMaterialSaving": "target loop should know when material-saving stage has ended",
        "materialSavingLowAlphaStageStopShouldStop(materialSavingStageStopCandidate, currentBest: bestCandidate)": "stage stop must allow an already-best material-saving candidate to stop before normal targets",
        "version_material_saving_low_alpha_raw_fallback_changed": "raw fallback cache invalidation key",
        "version_material_saving_low_alpha_stage_stop_changed": "stage-stop cache invalidation key",
        "version_material_saving_low_alpha_stage_stop_current_best_changed": "current-best stage-stop cache invalidation key",
        "version_material_saving_low_alpha_best_saved_changed": "best saved material-saving low-alpha cache invalidation key",
        "version_material_saving_stage_stop_current_best_candidate_changed": "current material-saving best stage-stop cache invalidation key",
        "version_material_saving_stop_before_lower_targets_changed": "lower material-saving target stop cache invalidation key",
        "version_material_saving_low_alpha_polish_changed": "cache invalidation key",
    }
    missing = [label for marker, label in required.items() if marker not in (swift + build)]
    if missing:
        print("missing material-saving low-alpha markers: " + ", ".join(missing))
        return 1

    begin = swift.find("external_auto_nest_material_saving_low_alpha_polish_begin")
    allow = swift.find(
        "selectedMaterialTopupCandidate(from: materialSavingLowAlphaReadableCandidate, lowAlphaReadable: true, allowStrictReadableLowAlphaPolish: true)"
    )
    accept = swift.find("external_auto_nest_material_saving_low_alpha_polish_accept")
    final_select = swift.find("external_auto_nest_candidate_pool_selected")
    if min(begin, allow, accept, final_select) < 0:
        print("missing material-saving low-alpha ordering markers")
        return 1
    if not (begin < allow < accept < final_select):
        print("material-saving low-alpha polish must run before final candidate selection")
        return 1

    raw_accept = swift.find("external_auto_nest_material_saving_low_alpha_raw_accept")
    raw_reject = swift.find("external_auto_nest_material_saving_low_alpha_raw_reject")
    if min(raw_accept, raw_reject) < 0:
        print("missing material-saving low-alpha raw fallback ordering markers")
        return 1
    if not (begin < raw_accept < final_select and begin < raw_reject < final_select):
        print("material-saving low-alpha raw fallback must run before final candidate selection")
        return 1

    stage_stop = swift.find("external_auto_nest_material_saving_low_alpha_stop_before_normal_targets")
    is_current_primary = swift.find("let isCurrentPrimaryTarget")
    if min(stage_stop, is_current_primary) < 0:
        print("missing material-saving low-alpha stage-stop ordering markers")
        return 1
    if not (stage_stop < is_current_primary < begin):
        print("material-saving low-alpha stage stop must run after the material-saving stage and before normal target checks")
        return 1

    helper = swift[
        swift.find("func materialSavingLowAlphaPolishShouldReplaceBest"):
        swift.find("func materialSavingLowAlphaCandidateShouldReplaceBest")
    ]
    helper_markers = {
        "polishedCandidate.materialSavingTarget": "replacement helper must only accept material-saving polished candidates",
        "selectedStrictReadableLowAlphaPolishGate(polishedCandidate)": "replacement helper must reuse strict low-alpha gate",
        "currentBest.alpha >= primaryMaterialProtectAlpha": "replacement helper must not replace protected high-alpha bests",
        "polishedCandidate.alpha > currentBest.alpha": "replacement helper should require material gain over the current best",
    }
    missing_helper = [label for marker, label in helper_markers.items() if marker not in helper]
    if missing_helper:
        print("missing replacement helper guards: " + ", ".join(missing_helper))
        return 1

    raw_helper = swift[
        swift.find("func materialSavingLowAlphaCandidateShouldReplaceBest"):
        swift.find("func selectedMaterialTopupCandidate")
    ]
    raw_helper_markers = {
        "candidate.materialSavingTarget": "raw helper must only accept material-saving candidates",
        "selectedStrictReadableLowAlphaPolishGate(candidate)": "raw helper must reuse strict low-alpha gate",
        "currentBest.alpha >= primaryMaterialProtectAlpha": "raw helper must not replace protected high-alpha bests",
        "candidate.alpha > currentBest.alpha": "raw helper should require material gain over the current best",
    }
    missing_raw_helper = [label for marker, label in raw_helper_markers.items() if marker not in raw_helper]
    if missing_raw_helper:
        print("missing raw fallback helper guards: " + ", ".join(missing_raw_helper))
        return 1

    stage_stop_helper = swift[
        swift.find("func materialSavingLowAlphaStageStopShouldStop"):
        swift.find("func selectedMaterialTopupCandidate")
    ]
    stage_stop_markers = {
        "candidate.materialSavingTarget": "stage stop helper must only accept material-saving candidates",
        "selectedStrictReadableLowAlphaPolishGate(candidate)": "stage stop helper must reuse strict low-alpha gate",
        "currentBest.alpha >= primaryMaterialProtectAlpha": "stage stop helper must not stop before protected high-alpha bests",
        "candidate.alpha >= currentBest.alpha - 0.0005": "stage stop helper must allow the saved candidate to already be currentBest",
    }
    missing_stage_stop = [label for marker, label in stage_stop_markers.items() if marker not in stage_stop_helper]
    if missing_stage_stop:
        print("missing stage-stop helper guards: " + ", ".join(missing_stage_stop))
        return 1

    stage_candidate_helper = swift[
        swift.find("func materialSavingStageStopCandidate"):
        swift.find("func materialSavingLowAlphaCandidateShouldReplaceSaved")
    ]
    stage_candidate_markers = {
        "currentBest.materialSavingTarget": "stage candidate helper must consider current material-saving best",
        "selectedStrictReadableLowAlphaPolishGate(currentBest)": "stage candidate helper must apply the strict readable low-alpha gate to current best",
        "savedLowAlpha.alpha": "stage candidate helper must compare against the saved low-alpha candidate",
        "currentBestCandidate.alpha >= savedLowAlpha.alpha - 0.0005": "stage candidate helper must prefer the current best when it ties or beats saved low-alpha",
    }
    missing_stage_candidate = [label for marker, label in stage_candidate_markers.items() if marker not in stage_candidate_helper]
    if missing_stage_candidate:
        print("missing material-saving stage-stop candidate guards: " + ", ".join(missing_stage_candidate))
        return 1

    saved_helper = swift[
        swift.find("func materialSavingLowAlphaCandidateShouldReplaceSaved"):
        swift.find("func materialSavingLowAlphaPolishShouldReplaceBest")
    ]
    saved_helper_markers = {
        "candidate.materialSavingTarget": "saved helper must only track material-saving candidates",
        "guard let saved else { return true }": "saved helper should accept the first material-saving candidate",
        "candidate.alpha > saved.alpha + 0.0005": "saved helper should prefer higher alpha over later lower-target candidates",
        "candidate.selectionScore > saved.selectionScore": "saved helper should use selection score only as an alpha tie-breaker",
    }
    missing_saved_helper = [label for marker, label in saved_helper_markers.items() if marker not in saved_helper]
    if missing_saved_helper:
        print("missing material-saving saved-candidate helper guards: " + ", ".join(missing_saved_helper))
        return 1

    stage_stop_call = swift[
        swift.find("let nextTargetIsMaterialSaving"):
        swift.find("let isCurrentPrimaryTarget")
    ]
    if "materialSavingStageStopCandidate(savedLowAlpha: materialSavingLowAlphaReadableCandidate, currentBest: bestCandidate)" not in stage_stop_call:
        print("stage stop must use the best material-saving stage-stop candidate")
        return 1
    lower_stop = swift.find("external_auto_nest_material_saving_low_alpha_stop_before_lower_targets")
    normal_stop = swift.find("external_auto_nest_material_saving_low_alpha_stop_before_normal_targets")
    if min(lower_stop, normal_stop, is_current_primary) < 0:
        print("missing material-saving lower-target stop ordering markers")
        return 1
    if not (lower_stop < normal_stop < is_current_primary):
        print("material-saving lower-target stop must run before the final normal-ladder stop")
        return 1
    lower_stage_stop_call = swift[swift.find("let nextTargetIsMaterialSaving"):normal_stop]
    if "nextTargetIsMaterialSaving," not in lower_stage_stop_call:
        print("lower-target stop must only run when the next target is still material-saving")
        return 1
    if "materialSavingLowAlphaStageStopShouldStop(materialSavingStageStopCandidate, currentBest: bestCandidate)" not in lower_stage_stop_call:
        print("lower-target stop must reuse the same strict material-saving stage-stop guard")
        return 1

    material_polish = swift[
        swift.find("if let materialSavingLowAlphaReadableCandidate"):
        swift.find("if let lowAlphaReadableCandidate,")
    ]
    if "materialSavingLowAlphaReadableCandidate" not in material_polish:
        print("material-saving low-alpha polish must use the saved material-saving low-alpha candidate")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
