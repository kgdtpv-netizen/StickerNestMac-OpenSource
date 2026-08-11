#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required_markers = {
        "STICKERNEST_EXTERNAL_FALLBACK_MATERIAL_TOPUP": "fallback material top-up env gate",
        "fallbackMaterialTopupEnabled": "fallback material top-up enabled flag",
        "fallbackMaterialTopupTargetAlpha": "fallback material top-up target alpha",
        "fallbackMaterialTopupMinAccept": "fallback material top-up minimum accept alpha",
        "fallbackMaterialTopupMinGain": "fallback material top-up minimum gain",
        "fallbackMaterialTopupMinVisualScore": "fallback material top-up visual floor",
        "fallbackMaterialTopupMaxMoves": "fallback material top-up move cap",
        "fallbackMaterialTopupMaxNudge": "fallback material top-up nudge cap",
        "isFallbackMaterialTopupAttempt": "fallback attempt gate",
        "!isPrimaryTarget": "fallback top-up must be lower target only",
        "attemptSeed.reusedPrimarySeed": "fallback top-up must use proven reused primary seed",
        "!attemptVariant.readableVariant": "fallback top-up must not run on readable no-rotate variant",
        "attemptMaterialTopupTargetAlpha": "per-attempt material top-up target",
        "attemptMaterialTopupMinAccept": "per-attempt material top-up min accept",
        "attemptMaterialTopupMinGain": "per-attempt material top-up min gain",
        "attemptMaterialTopupMinVisualScore": "per-attempt visual floor",
        "fallbackMaterialTopup=\\(isFallbackMaterialTopupAttempt)": "attempt log records fallback material top-up",
        "0.5460": "fallback default target should stay modest",
        "0.5430": "fallback default accept should be below primary 55% floor",
        "localAdapterForAttempt": "fallback default should not spend local-adapter runtime",
        "version_fallback_material_topup_changed": "cache invalidation key",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing fallback material top-up markers: " + ", ".join(missing))
        return 1

    fallback_gate = source.find("let isFallbackMaterialTopupAttempt")
    material_gate = source.find("let materialTopupForAttempt", fallback_gate)
    env_gate = source.find("environment[\"STICKERNEST_MATERIAL_ALPHA_TOPUP\"]", material_gate)
    if min(fallback_gate, material_gate, env_gate) < 0:
        print("missing fallback or material top-up gate ordering")
        return 1
    if not (fallback_gate < material_gate < env_gate):
        print("fallback material top-up gate should feed the generic material top-up env")
        return 1

    gate_body = source[fallback_gate:material_gate]
    required_gate_markers = {
        "fallbackMaterialTopupEnabled": "must respect fallback env gate",
        "!isPrimaryTarget": "must be fallback-only",
        "lowerTargetDelta >= fallbackMaterialTopupMinDeltaMM": "must require far enough fallback",
        "attemptSeed.reusedPrimarySeed": "must only reuse proven primary seed",
        "!attemptVariant.readableVariant": "must not top-up readable no-rotate variant",
        "manualStaggerExternalMode": "must stay scoped to current manual-stagger production path",
    }
    missing_gate = [label for marker, label in required_gate_markers.items() if marker not in gate_body]
    if missing_gate:
        print("missing fallback gate markers: " + ", ".join(missing_gate))
        return 1

    primary_default_pos = source.find("let primaryMaterialTopupTargetAlpha")
    fallback_default_pos = source.find("let fallbackMaterialTopupTargetAlpha")
    target_env_pos = source.find("environment[\"STICKERNEST_MATERIAL_ALPHA_TOPUP_TARGET\"]", fallback_default_pos)
    if min(primary_default_pos, fallback_default_pos, target_env_pos) < 0:
        print("missing target-alpha wiring positions")
        return 1
    if not (primary_default_pos < fallback_default_pos < target_env_pos):
        print("fallback defaults should be declared before process env wiring")
        return 1

    forbidden = {
        "fallbackMaterialTopupMinAccept = primaryMaterialProtectAlpha": "fallback accept must not reuse primary 55% floor",
    }
    bad = [label for marker, label in forbidden.items() if marker in source]
    if bad:
        print("forbidden fallback material top-up markers: " + ", ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
