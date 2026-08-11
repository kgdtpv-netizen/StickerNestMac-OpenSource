#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()

    required_python = {
        "STICKERNEST_MANUAL_STAGGER_SAFE_ROTATE": "safe-angle Python env gate",
        "MANUAL_STAGGER_SAFE_ROTATE": "safe-angle Python flag",
        "SAFE_MANUAL_STAGGER_ANGLES": "safe-angle allowlist",
        "[30,330]": "safe-angle adds only readable 30-degree diagonals",
        "\"manual_stagger_safe_rotate\"": "safe-angle JSON marker",
    }
    missing_python = [label for marker, label in required_python.items() if marker not in source]
    if missing_python:
        print("missing safe-angle Python markers: " + ", ".join(missing_python))
        return 1

    safe_gate_pos = source.find("if MANUAL_STAGGER and MANUAL_STAGGER_ROTATE:")
    safe_flag_pos = source.find("MANUAL_STAGGER_SAFE_ROTATE", safe_gate_pos)
    broad_angles_pos = source.find("[30,330,90,270,180,75,285,105,255]", safe_gate_pos)
    if min(safe_gate_pos, safe_flag_pos, broad_angles_pos) < 0:
        print("missing safe-angle angle-gate ordering markers")
        return 1
    if not (safe_gate_pos < safe_flag_pos < broad_angles_pos):
        print("safe-angle branch should be checked before broad manual-stagger angles")
        return 1

    safe_branch = source[safe_flag_pos:broad_angles_pos]
    forbidden_safe_angles = ["90", "270", "180", "75", "285", "105", "255"]
    leaked = [angle for angle in forbidden_safe_angles if angle in safe_branch]
    if leaked:
        print("safe-angle branch leaked hard rotation angles: " + ", ".join(leaked))
        return 1

    required_swift = {
        "STICKERNEST_EXTERNAL_SAFE_ANGLE_RESCUE": "safe-angle Swift env gate",
        "safeAngleRescueEnabled": "safe-angle Swift enabled flag",
        "safeAngleRescueMinAlpha": "safe-angle narrow alpha floor",
        "safeAngleRescueMaterialTopupTargetAlpha": "safe-angle material top-up target",
        "safeAngleRescueMaterialTopupMinAccept": "safe-angle material top-up accept floor",
        "safeAngleRescueMaterialTopupMaxDeficit": "safe-angle material top-up deficit window",
        "safeAngleRescueScaleTransferMinAccept": "safe-angle scale-transfer accept floor",
        "safeAngleVariant": "attempt variant records safe-angle mode",
        "-safeangle": "safe-angle output path suffix",
        "safe_angle": "safe-angle attempt log label",
        "shouldRunSafeAngleRescueVariant": "safe-angle attempt predicate",
        "isSafeAngleRescueMaterialTopupAttempt": "safe-angle material top-up attempt predicate",
        "primaryMaterialFastStopDeferredForSafeAngle": "normal fast-stop must wait for safe-angle sibling",
        "external_auto_nest_primary_material_fast_stop_deferred_for_safe_angle": "safe-angle fast-stop defer audit log",
        "external_auto_nest_safe_angle_rescue_begin": "safe-angle audit log",
        "external_auto_nest_safe_angle_rescue_alpha_floor": "safe-angle alpha-floor audit log",
        'environment["STICKERNEST_MANUAL_STAGGER_SAFE_ROTATE"] = "0"': "Swift keeps broad search available for strict readable rescue",
        "STICKERNEST_HARD_REJECT_UPSIDE_RATIO": "Swift hard-reject upside env",
        "STICKERNEST_HARD_REJECT_SIDEWAYS_RATIO": "Swift hard-reject sideways env",
        "STICKERNEST_HARD_REJECT_HARD_RATIO": "Swift hard-reject hard env",
        "STICKERNEST_HARD_REJECT_MIN_READABLE_RATIO": "Swift hard-reject readable floor env",
        "STICKERNEST_MAX_UPSIDE_RATIO": "Swift readable guard upside env",
        "STICKERNEST_MAX_SIDEWAYS_RATIO": "Swift readable guard sideways env",
        "STICKERNEST_MAX_HARD_OTHER_RATIO": "Swift readable guard hard env",
        "version_safe_angle_rescue_changed": "safe-angle cache invalidation key",
    }
    missing_swift = [label for marker, label in required_swift.items() if marker not in swift_source]
    if missing_swift:
        print("missing safe-angle Swift markers: " + ", ".join(missing_swift))
        return 1

    variant_pos = swift_source.find("struct ExternalAttemptVariant")
    predicate_pos = swift_source.find("let shouldRunSafeAngleRescueVariant", variant_pos)
    variants_pos = swift_source.find("let attemptVariants", predicate_pos)
    env_pos = swift_source.find('if attemptVariant.safeAngleVariant', variants_pos)
    cache_pos = swift_source.find("version_safe_angle_rescue_changed")
    bridge_cache_pos = swift_source.find("version_high_readable_rescue_alpha_bridge_changed")
    if min(variant_pos, predicate_pos, variants_pos, env_pos, cache_pos, bridge_cache_pos) < 0:
        print("missing safe-angle Swift ordering markers")
        return 1
    if not (variant_pos < predicate_pos < variants_pos < env_pos):
        print("safe-angle variant should be decided before external process env wiring")
        return 1
    if not (cache_pos < bridge_cache_pos):
        print("safe-angle cache invalidation should run before older v210 high-readable cache invalidation")
        return 1

    predicate_block = swift_source[predicate_pos:variants_pos]
    required_predicate = {
        "safeAngleRescueEnabled": "must respect env gate",
        "manualStaggerExternalMode": "must stay scoped to manual-stagger mode",
        "isPrimaryMaterialTopupAttempt": "must run only on bounded primary material seed attempts",
        "attemptSeed.reusedPrimarySeed == false": "must not multiply fallback reused-seed runtime",
        "bestCandidate?.audit.score ?? 0": "must only rescue when visual score still needs help",
    }
    missing_predicate = [label for marker, label in required_predicate.items() if marker not in predicate_block]
    if missing_predicate:
        print("missing safe-angle predicate guards: " + ", ".join(missing_predicate))
        return 1

    material_predicate_pos = swift_source.find("let isSafeAngleRescueMaterialTopupAttempt", variants_pos)
    material_gate_pos = swift_source.find("let materialTopupForAttempt", material_predicate_pos)
    if min(material_predicate_pos, material_gate_pos) < 0:
        print("missing safe-angle material top-up predicate ordering")
        return 1
    material_predicate_block = swift_source[material_predicate_pos:material_gate_pos]
    required_material_predicate = {
        "safeAngleRescueEnabled": "must respect safe-angle env gate",
        "attemptVariant.safeAngleVariant": "must only apply to safe-angle variant",
        "isPrimaryMaterialTopupAttempt": "must remain bounded to primary material seed attempts",
    }
    missing_material_predicate = [label for marker, label in required_material_predicate.items() if marker not in material_predicate_block]
    if missing_material_predicate:
        print("missing safe-angle material predicate guards: " + ", ".join(missing_material_predicate))
        return 1

    env_block = swift_source[env_pos:swift_source.find("process.environment = environment", env_pos)]
    if 'environment["STICKERNEST_MANUAL_STAGGER_SAFE_ROTATE"] = "1"' in env_block:
        print("safe-angle Swift variant must not narrow Python angle search; strict hard-reject guards provide readability")
        return 1
    required_env_values = {
        'environment["STICKERNEST_MANUAL_STAGGER_ROTATE"] = "1"': "safe-angle rescue should keep rotation search enabled",
        'environment["STICKERNEST_HARD_REJECT_UPSIDE_RATIO"] = "0.0"': "upside hard reject must be zero",
        'environment["STICKERNEST_HARD_REJECT_SIDEWAYS_RATIO"] = "0.0"': "sideways hard reject must be zero",
        'environment["STICKERNEST_HARD_REJECT_HARD_RATIO"] = "0.0"': "hard-orientation reject must be zero",
        'environment["STICKERNEST_HARD_REJECT_MIN_READABLE_RATIO"] = "0.95"': "readable hard floor must stay high",
        'environment["STICKERNEST_MAX_UPSIDE_RATIO"] = "0.0"': "readability upside max must be zero",
        'environment["STICKERNEST_MAX_SIDEWAYS_RATIO"] = "0.0"': "readability sideways max must be zero",
        'environment["STICKERNEST_MAX_HARD_OTHER_RATIO"] = "0.0"': "readability hard max must be zero",
    }
    missing_env = [label for marker, label in required_env_values.items() if marker not in env_block]
    if missing_env:
        print("missing safe-angle strict env values: " + ", ".join(missing_env))
        return 1

    material_env_pos = swift_source.find('environment["STICKERNEST_MATERIAL_ALPHA_TOPUP_TARGET"]', material_gate_pos)
    scale_env_pos = swift_source.find('environment["STICKERNEST_SCALE_TRANSFER_MIN_ACCEPT"]', material_env_pos)
    if min(material_env_pos, scale_env_pos) < 0:
        print("missing safe-angle material env wiring positions")
        return 1
    material_env_block = swift_source[material_predicate_pos:scale_env_pos]
    required_material_env = {
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueMaterialTopupTargetAlpha": "safe-angle top-up target must not use 55% primary target",
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueMaterialTopupMinAccept": "safe-angle top-up accept must use safe floor",
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueMaterialTopupMinGain": "safe-angle top-up gain must use safe floor",
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueMaterialTopupMaxMoves": "safe-angle top-up moves must be explicit",
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueMaterialTopupMaxNudge": "safe-angle top-up nudge must be explicit",
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueMaterialTopupMinVisualScore": "safe-angle visual floor must be explicit",
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueMaterialTopupTargetAlpha": "safe-angle multi-piece target must use safe target",
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueMaterialTopupMinAccept": "safe-angle multi-piece accept must use safe floor",
        "isSafeAngleRescueMaterialTopupAttempt ? safeAngleRescueScaleTransferMinAccept": "safe-angle scale transfer must use safe floor",
        "STICKERNEST_MATERIAL_ALPHA_TOPUP_MAX_DEFICIT": "safe-angle must pass a deficit window",
    }
    missing_material_env = [label for marker, label in required_material_env.items() if marker not in material_env_block]
    if missing_material_env:
        print("missing safe-angle material env markers: " + ", ".join(missing_material_env))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
