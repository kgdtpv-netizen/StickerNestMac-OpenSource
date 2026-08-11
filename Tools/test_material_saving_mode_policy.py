#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
BUILD = ROOT / "build.zsh"


def missing(markers: dict[str, str], source: str) -> list[str]:
    return [label for marker, label in markers.items() if marker not in source]


def main() -> int:
    swift = SWIFT.read_text()
    build = BUILD.read_text()

    required = {
        'static let version = "1.1.244"': "AppInfo version should be bumped",
        'static let build = "20260607.005"': "AppInfo build should be bumped",
        "var materialSavingMode = false": "settings should expose opt-in material-saving mode",
        'Toggle("省料优先", isOn: $model.settings.materialSavingMode)': "UI should expose explicit opt-in toggle",
        "materialSavingMode=\\(materialSavingMode)": "settings log should include material-saving mode",
        "STICKERNEST_EXTERNAL_MATERIAL_SAVING_MODE": "env override for material-saving mode",
        "materialSavingModeRequested": "default-off requested flag",
        "materialSavingModeEnabled": "enabled flag should be derived from request and external mode",
        "settings.isTemplateMaterial && (settings.gapMM >= 5.5 || materialSavingModeRequested)": "opt-in mode should still use the guarded external A2 path when relaxing gap",
        "STICKERNEST_EXTERNAL_MATERIAL_SAVING_GAP_MM": "gap override env",
        "materialSavingGapMM": "bounded gap-relaxed value",
        "STICKERNEST_EXTERNAL_MATERIAL_SAVING_TARGETS": "target ladder env",
        "materialSavingTargetValues": "bounded target ladder",
        "STICKERNEST_EXTERNAL_MATERIAL_SAVING_SECONDS": "bounded seconds env",
        "materialSavingSeconds": "independent material-saving budget",
        "materialSavingAttemptSeeds": "bounded seed list",
        "struct ExternalTargetCandidate": "target candidates should carry gap and mode metadata",
        "let gapMM: Double?": "target candidate should support gap override",
        "let materialSaving: Bool": "target candidate should mark material-saving attempts",
        "var outputNameToken": "target candidate output filenames should include gap metadata",
        "addTarget(target, gapMM: materialSavingGapMM, materialSaving: true)": "target ladder should insert gap-relaxed candidates",
        "external_auto_nest_material_saving_target_begin": "audit log for material-saving target",
        "attemptSettings.gapMM = gapMM": "target candidate should override solver gap only for that attempt",
        "let isMaterialSavingTarget = targetCandidate.materialSaving": "per-target material-saving predicate",
        "isMaterialSavingTarget ? materialSavingAttemptSeeds.count": "material-saving target should use bounded seed count",
        "for seed in materialSavingAttemptSeeds": "material-saving target should run explicit seeds",
        "attemptSeconds = materialSavingSeconds": "material-saving target should use its own time budget",
        "isMaterialSavingTarget ? [ExternalAttemptVariant(readableVariant: true, manualRotate: false, safeAngleVariant: false)]": "material-saving target should run strict readable no-rotate variant",
        "materialSaving=\\(isMaterialSavingTarget)": "attempt logs should expose material-saving status",
        "targets=\\(targetCandidates.map { $0.logText }.joined(separator: \",\"))": "begin log should include target gap metadata",
        "version_material_saving_mode_changed": "cache invalidation key",
    }
    missing_swift = missing(required, swift)
    if missing_swift:
        print("missing material-saving markers: " + ", ".join(missing_swift))
        return 1

    if 'marketing_version="1.1.244"' not in build:
        print("build.zsh marketing version should be bumped to 1.1.244")
        return 1

    mode_pos = swift.find("materialSavingModeRequested")
    edge_pos = swift.find("let edgeSafetyExternalMode")
    target_pos = swift.find("var targetCandidates: [ExternalTargetCandidate] = []")
    add_saving_pos = swift.find("addTarget(target, gapMM: materialSavingGapMM, materialSaving: true)", target_pos)
    add_standard_pos = swift.find("[settings.targetLongSideMM, 112.5, 112.0, 111.0]", target_pos)
    if min(mode_pos, edge_pos, target_pos, add_saving_pos, add_standard_pos) < 0:
        print("missing target ordering markers")
        return 1
    if not (mode_pos < edge_pos < target_pos < add_saving_pos < add_standard_pos):
        print("material-saving targets must be gated and inserted before the normal 6mm target ladder")
        return 1

    cache_pos = swift.find("version_material_saving_mode_changed")
    strict_material_pos = swift.find("version_selected_strict_readable_material_polish_changed")
    if min(cache_pos, strict_material_pos) < 0:
        print("missing cache ordering markers")
        return 1
    if not (cache_pos < strict_material_pos):
        print("material-saving cache invalidation should run before v1.1.235 cache checks")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
