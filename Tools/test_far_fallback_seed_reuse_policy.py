#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required_markers = {
        "STICKERNEST_EXTERNAL_FAR_FALLBACK_REUSE_PRIMARY_SEEDS": "far fallback primary-seed reuse env gate",
        "farFallbackReusePrimarySeedsEnabled": "far fallback primary-seed reuse enabled flag",
        "STICKERNEST_EXTERNAL_FAR_FALLBACK_REUSE_MIN_DELTA_MM": "far fallback reuse min-delta env",
        "farFallbackReuseMinDeltaMM": "far fallback reuse min-delta setting",
        "ExternalAttemptSeed": "explicit attempt seed model",
        "seenAttemptSeeds": "explicit duplicate-seed guard",
        "reusedPrimarySeed": "attempts record reused primary seed state",
        "external_auto_nest_reused_primary_seed": "log when a lower target reuses a primary seed",
        "version_far_fallback_seed_reuse_changed": "cache invalidation key",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing far fallback seed reuse policy markers: " + ", ".join(missing))
        return 1

    if "let seed = attemptSeed.seed" not in source or "let seedIndex = attemptSeed.seedIndex" not in source:
        print("external attempts should use explicit attemptSeed values, not only target-number seed derivation")
        return 1

    reused_seed4 = "appendAttemptSeed(seedIndex: 4, seed: 4, reusedPrimarySeed: true)"
    normal_seed_append = "appendAttemptSeed(seedIndex: seedIndex, seed: stableSeedBase + seedIndex, reusedPrimarySeed: false)"
    reused_pos = source.find(reused_seed4)
    normal_pos = source.find(normal_seed_append, reused_pos)
    if min(reused_pos, normal_pos) < 0 or reused_pos > normal_pos:
        print("far fallback should append reused primary seed4 before target-number fallback seeds")
        return 1

    if "(!shouldRunReadableNoRotateVariant || attemptVariant.readableVariant)" not in source:
        print("lower fast-stop must not skip the readable no-rotate variant for reused fallback seeds")
        return 1

    reuse_pos = source.find("external_auto_nest_reused_primary_seed")
    variant_pos = source.find("fallbackReadableVariantsEnabled")
    run_pos = source.find("try process.run()", reuse_pos)
    if min(reuse_pos, variant_pos, run_pos) < 0:
        print("missing seed-reuse/readable-variant/process ordering markers")
        return 1
    if not (variant_pos < reuse_pos < run_pos):
        print("reused primary seed should be chosen before running the external readable/normal variants")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
