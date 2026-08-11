#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
BUILD = ROOT / "build.zsh"


def require(markers: dict[str, str], source: str, prefix: str) -> list[str]:
    return [label for marker, label in markers.items() if marker not in source]


def main() -> int:
    swift = SWIFT.read_text()
    build = BUILD.read_text()

    missing = require(
        {
            'static let version = "1.1.244"': "AppInfo version should be bumped",
            'static let build = "20260607.005"': "AppInfo build should be bumped",
            "STICKERNEST_EXTERNAL_SAFE_ANGLE_HIGH_TARGET": "high-target env gate",
            "safeAngleHighTargetEnabled": "high-target enabled flag",
            "safeAngleHighTargetMM": "high-target default size",
            "safeAngleHighTargetMinDeltaMM": "high-target minimum delta guard",
            "STICKERNEST_EXTERNAL_SAFE_ANGLE_HIGH_TARGET_SECONDS": "high-target independent seconds env",
            "safeAngleHighTargetDefaultSeconds": "high-target default short budget",
            "safeAngleHighTargetSeconds": "high-target independent seconds value",
            "isSafeAngleHighTarget": "per-target high-target predicate",
            "isSafeAngleHighTargetAttempt": "per-seed high-target attempt predicate",
            "safeAngleHighTargetAttemptSeeds": "bounded high-target seed list",
            "external_auto_nest_safe_angle_high_target_begin": "high-target audit log",
            "version_safe_angle_high_target_changed": "cache invalidation key",
        },
        swift,
        "Swift",
    )
    if 'marketing_version="1.1.244"' not in build:
        missing.append("build.zsh marketing version should be bumped")
    if missing:
        print("missing safe-angle high-target markers: " + ", ".join(missing))
        return 1

    target_pos = swift.find("var targetCandidates: [ExternalTargetCandidate] = []")
    high_add_pos = swift.find("addTarget(safeAngleHighTargetMM)", target_pos)
    primary_add_pos = swift.find("[settings.targetLongSideMM, 112.5, 112.0, 111.0]", target_pos)
    if min(target_pos, high_add_pos, primary_add_pos) < 0:
        print("missing target-list ordering markers")
        return 1
    if not (target_pos < high_add_pos < primary_add_pos):
        print("safe-angle high target must be tried before the standard primary target")
        return 1

    target_block = swift[target_pos:swift.find("AppLogger.shared.log(\"external_auto_nest_begin", target_pos)]
    required_target_block = {
        "safeAngleHighTargetEnabled": "target insertion must be gated",
        "safeAngleHighTargetMM > settings.targetLongSideMM + safeAngleHighTargetMinDeltaMM": "target must be a real enlargement",
        "addTarget(safeAngleHighTargetMM)": "target list should include high target",
    }
    missing_target = require(required_target_block, target_block, "target block")
    if missing_target:
        print("missing high-target insertion guards: " + ", ".join(missing_target))
        return 1

    seed_pos = swift.find("let isSafeAngleHighTarget", target_pos)
    variants_pos = swift.find("let baseAttemptVariants", seed_pos)
    if min(seed_pos, variants_pos) < 0:
        print("missing high-target seed/variant ordering")
        return 1
    seed_block = swift[seed_pos:variants_pos]
    required_seed_block = {
        "safeAngleHighTargetAttemptSeeds": "high target should use a bounded seed list",
        "appendAttemptSeed(seedIndex: seed, seed: seed, reusedPrimarySeed: false)": "high target should run explicit real seeds",
        "isSafeAngleHighTargetAttempt": "high target attempt predicate should be computed before variants",
    }
    missing_seed = require(required_seed_block, seed_block, "seed block")
    if missing_seed:
        print("missing high-target seed guards: " + ", ".join(missing_seed))
        return 1

    seconds_pos = swift.find("let safeAngleHighTargetDefaultSeconds")
    log_pos = swift.find("external_auto_nest_begin", seconds_pos)
    if min(seconds_pos, log_pos) < 0:
        print("missing high-target seconds wiring")
        return 1
    seconds_block = swift[seconds_pos:log_pos]
    required_seconds_block = {
        "min(primaryExtraSeedSeconds, 45.0)": "default high-target budget should be shorter than broad primary extra seeds",
        'ProcessInfo.processInfo.environment["STICKERNEST_EXTERNAL_SAFE_ANGLE_HIGH_TARGET_SECONDS"]': "high-target budget must be env-overridable",
        "max(5.0, min(primaryExtraSeedSeconds": "high-target budget should be bounded by primary extra seed budget",
    }
    missing_seconds = require(required_seconds_block, seconds_block, "seconds block")
    if missing_seconds:
        print("missing high-target seconds guards: " + ", ".join(missing_seconds))
        return 1
    log_block = swift[log_pos:swift.find("for (attemptIndex", log_pos)]
    if "safeAngleHighTargetSeconds=" not in log_block:
        print("external begin log must expose high-target seconds")
        return 1

    stable_seed_pos = swift.find("let stableSeedBase", target_pos)
    if stable_seed_pos < 0:
        print("missing stable seed base calculation")
        return 1
    stable_seed_block = swift[stable_seed_pos:swift.find("var attemptSeeds", stable_seed_pos)]
    if "isPrimaryTarget ? 0 : stableLowerTargetSeedBase" not in stable_seed_block:
        print("primary target seeds must stay 0-4 even when the high target is inserted first")
        return 1

    variant_block = swift[variants_pos:swift.find("let attemptVariants", variants_pos)]
    if "isSafeAngleHighTargetAttempt ? []" not in variant_block:
        print("safe-angle high target should skip the normal broad-rotation variant")
        return 1

    attempt_seconds_pos = swift.find("let attemptSeconds: Double", seed_pos)
    variants_guard_pos = swift.find("let shouldRunReadableNoRotateVariant", attempt_seconds_pos)
    if min(attempt_seconds_pos, variants_guard_pos) < 0:
        print("missing attempt seconds block")
        return 1
    attempt_seconds_block = swift[attempt_seconds_pos:variants_guard_pos]
    if "attemptSeconds = safeAngleHighTargetSeconds" not in attempt_seconds_block:
        print("safe-angle high target must use its independent short budget")
        return 1

    safe_predicate_pos = swift.find("let shouldRunSafeAngleRescueVariant", seed_pos)
    attempt_variants_pos = swift.find("let attemptVariants", safe_predicate_pos)
    safe_predicate_block = swift[safe_predicate_pos:attempt_variants_pos]
    for marker, label in {
        "isPrimaryMaterialTopupAttempt || isSafeAngleHighTargetAttempt": "safe-angle variant should run for high target",
        "attemptSeed.reusedPrimarySeed == false": "safe-angle high target must not multiply fallback reused seeds",
    }.items():
        if marker not in safe_predicate_block:
            print("missing safe-angle high-target predicate marker: " + label)
            return 1

    material_pos = swift.find("let isSafeAngleRescueMaterialTopupAttempt", variants_pos)
    material_block = swift[material_pos:swift.find("let materialTopupForAttempt", material_pos)]
    if "isPrimaryMaterialTopupAttempt || isSafeAngleHighTargetAttempt" not in material_block:
        print("safe-angle high target must use safe-angle material top-up floors")
        return 1

    cache_pos = swift.find("version_safe_angle_high_target_changed")
    old_cache_pos = swift.find("version_safe_angle_rescue_changed")
    if min(cache_pos, old_cache_pos) < 0:
        print("missing high-target cache ordering markers")
        return 1
    if not (cache_pos < old_cache_pos):
        print("high-target cache invalidation should run before v1.1.211 safe-angle cache invalidation")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
