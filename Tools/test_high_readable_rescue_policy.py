#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required_markers = {
        "STICKERNEST_EXTERNAL_HIGH_READABLE_RESCUE": "high readable rescue env gate",
        "highReadableRescueEnabled": "high readable rescue enabled flag",
        "highReadableRescueTargetMM": "high readable rescue target",
        "108.0": "default 108mm readable rescue target",
        "highReadableRescueMinDeltaMM": "high readable rescue minimum target delta",
        "5.0": "default 5mm rescue delta reaches 108mm from 113.3mm",
        "highReadableRescueMinAlpha": "high readable rescue minimum alpha floor",
        "0.500": "default rescue alpha floor",
        "STICKERNEST_EXTERNAL_HIGH_READABLE_RESCUE_MATERIAL_TOPUP": "high readable rescue material topup env gate",
        "highReadableRescueMaterialTopupEnabled": "high readable rescue material topup enabled flag",
        "highReadableRescueMaterialTopupTargetAlpha": "high readable rescue material topup target",
        "STICKERNEST_EXTERNAL_HIGH_READABLE_RESCUE_MATERIAL_TOPUP_MAX_DEFICIT": "high readable rescue material topup max deficit env gate",
        "highReadableRescueMaterialTopupMaxDeficit": "high readable rescue material topup max deficit",
        "STICKERNEST_EXTERNAL_HIGH_READABLE_RESCUE_SWIFT_ALPHA_TOLERANCE": "high readable rescue Swift alpha tolerance env gate",
        "highReadableRescueSwiftAlphaTolerance": "high readable rescue Swift alpha tolerance",
        "highReadableRescueSwiftAlphaBridgeOK": "high readable rescue Swift/JSON alpha bridge predicate",
        "external_auto_nest_high_readable_rescue_alpha_bridge": "high readable rescue alpha bridge audit log",
        "isHighReadableRescueMaterialTopupAttempt": "readable rescue material topup attempt predicate",
        "STICKERNEST_MATERIAL_ALPHA_TOPUP_MAX_DEFICIT": "python material topup max deficit pass-through",
        "isHighReadableRescueTarget": "per-target high readable rescue gate",
        "addTarget(highReadableRescueTargetMM)": "rescue target inserted into candidate list",
        "targetLongSideMM - highReadableRescueTargetMM": "rescue target exact match guard",
        "appendAttemptSeed(seedIndex: 4, seed: 4, reusedPrimarySeed: true)": "rescue target reuses proven seed4",
        "lowerTargetDelta >= highReadableRescueMinDeltaMM": "rescue target must be meaningfully lower than primary",
        "|| isHighReadableRescueTarget": "readable no-rotate variant runs for rescue target",
        "reason=high_readable_rescue_alpha_below_floor": "rescue alpha floor rejection log",
        "version_high_readable_rescue_changed": "cache invalidation key",
        "version_high_readable_rescue_topup_changed": "topup cache invalidation key",
        "version_high_readable_rescue_topup_deficit_changed": "topup max-deficit cache invalidation key",
        "version_high_readable_rescue_alpha_bridge_changed": "Swift/JSON alpha bridge cache invalidation key",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing high readable rescue markers: " + ", ".join(missing))
        return 1

    target_list_pos = source.find("addTarget(highReadableRescueTargetMM)")
    lower_target_pos = source.find("[105.0, 104.0, 102.0]")
    if min(target_list_pos, lower_target_pos) < 0 or target_list_pos > lower_target_pos:
        print("108mm readable rescue target should be inserted before 105/104/102 fallbacks")
        return 1

    rescue_gate_pos = source.find("let isHighReadableRescueTarget")
    seed_reuse_pos = source.find("appendAttemptSeed(seedIndex: 4, seed: 4, reusedPrimarySeed: true)", rescue_gate_pos)
    variant_pos = source.find("let shouldRunReadableNoRotateVariant", rescue_gate_pos)
    alpha_floor_pos = source.find("high_readable_rescue_alpha_below_floor", variant_pos)
    if min(rescue_gate_pos, seed_reuse_pos, variant_pos, alpha_floor_pos) < 0:
        print("missing rescue gate ordering markers")
        return 1
    if not (rescue_gate_pos < seed_reuse_pos < variant_pos < alpha_floor_pos):
        print("rescue target should feed seed reuse, readable variant, then alpha floor rejection")
        return 1

    topup_predicate_pos = source.find("let isHighReadableRescueMaterialTopupAttempt", rescue_gate_pos)
    material_topup_pos = source.find("let materialTopupForAttempt", topup_predicate_pos)
    if min(topup_predicate_pos, material_topup_pos) < 0:
        print("missing high readable rescue material topup ordering markers")
        return 1
    if not (rescue_gate_pos < topup_predicate_pos < material_topup_pos):
        print("high readable rescue material topup predicate should feed materialTopupForAttempt")
        return 1
    predicate_block = source[topup_predicate_pos:material_topup_pos]
    predicate_required = {
        "highReadableRescueMaterialTopupEnabled": "topup env gate",
        "isHighReadableRescueTarget": "target gate",
        "attemptVariant.readableVariant": "readable/no-rotate gate",
    }
    missing_predicate = [label for marker, label in predicate_required.items() if marker not in predicate_block]
    if missing_predicate:
        print("missing high readable rescue material topup predicate markers: " + ", ".join(missing_predicate))
        return 1

    bridge_pos = source.find("let highReadableRescueSwiftAlphaBridgeOK", variant_pos)
    bridge_log_pos = source.find("external_auto_nest_high_readable_rescue_alpha_bridge", bridge_pos)
    if min(bridge_pos, bridge_log_pos) < 0:
        print("missing high readable rescue Swift/JSON alpha bridge markers")
        return 1
    bridge_block = source[bridge_pos:bridge_log_pos]
    bridge_required = {
        "attemptVariant.readableVariant": "readable/no-rotate gate",
        "externalAlpha": "external JSON alpha must be checked",
        "highReadableRescueMinAlpha": "external alpha floor",
        "highReadableRescueSwiftAlphaTolerance": "Swift alpha tolerance",
        "orientationStats.readable == items.count": "all items must be readable",
        "orientationStats.upside == 0": "no upside pieces",
        "orientationStats.sideways == 0": "no sideways pieces",
        "orientationStats.hard == 0": "no hard-orientation pieces",
    }
    missing_bridge = [label for marker, label in bridge_required.items() if marker not in bridge_block]
    if missing_bridge:
        print("missing high readable rescue Swift/JSON bridge guards: " + ", ".join(missing_bridge))
        return 1

    cache_pos = source.find("version_high_readable_rescue_changed")
    topup_cache_pos = source.find("version_high_readable_rescue_topup_changed")
    deficit_cache_pos = source.find("version_high_readable_rescue_topup_deficit_changed")
    bridge_cache_pos = source.find("version_high_readable_rescue_alpha_bridge_changed")
    previous_cache_pos = source.find("version_fallback_material_topup_changed")
    if min(cache_pos, topup_cache_pos, deficit_cache_pos, bridge_cache_pos, previous_cache_pos) < 0:
        print("missing high readable rescue cache invalidation markers")
        return 1
    if not (previous_cache_pos < bridge_cache_pos < deficit_cache_pos < topup_cache_pos < cache_pos):
        print("high readable rescue cache invalidation should check newest high-readable changes before older high-readable changes")
        return 1

    forbidden = {
        "highReadableRescueMinAlpha = acceptAlpha": "rescue alpha floor should be explicit and auditable",
        "highReadableRescueEnabled = true": "rescue must remain env-gated",
        "highReadableRescueMaterialTopupTargetAlpha = highReadableRescueMinAlpha": "rescue material topup target should be explicit and auditable",
        "highReadableRescueMaterialTopupMaxDeficit = 0.008": "rescue material topup max deficit must exceed the known 49.09% to 50.00% gap",
        "highReadableRescueSwiftAlphaTolerance = 0.0": "Swift/JSON alpha bridge tolerance must cover the known 50.02% JSON vs 49.9% Swift gap",
    }
    bad = [label for marker, label in forbidden.items() if marker in source]
    if bad:
        print("forbidden high readable rescue markers: " + ", ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
