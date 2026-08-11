#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
BUILD = ROOT / "build.zsh"


def require(text: str, marker: str, label: str) -> bool:
    if marker not in text:
        print(f"missing {label}: {marker}")
        return False
    return True


def require_order(text: str, earlier: str, later: str, label: str) -> bool:
    a = text.find(earlier)
    b = text.find(later)
    if a < 0 or b < 0 or a >= b:
        print(f"wrong order {label}: {earlier} before {later}")
        return False
    return True


def main() -> int:
    swift = SWIFT.read_text(encoding="utf-8")
    auto_nest = AUTO_NEST.read_text(encoding="utf-8")
    build = BUILD.read_text(encoding="utf-8")
    ok = True

    ok &= require(swift, 'static let version = "1.1.244"', "Swift app version")
    ok &= require(swift, 'static let build = "20260607.005"', "Swift app build")
    ok &= require(build, 'marketing_version="1.1.244"', "bundle marketing version")

    ok &= require(swift, "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE", "Swift external chain toggle")
    ok &= require(swift, 'lowAlphaReadableRightCenterVoidChainRelocateDefault = "1"', "Swift chain default")
    ok &= require(swift, "lowAlphaReadableRightCenterVoidChainRelocateEnabled = lowAlphaReadableRightCenterVoidRelocateEnabled", "Swift chain gated by right-center pass")
    ok &= require(swift, "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN", "Swift chain min alpha gain knob")
    ok &= require(swift, "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN", "Swift chain min void gain knob")
    ok &= require(swift, "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT", "Swift chain node limit knob")
    ok &= require(swift, "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL", "Swift second-backfill toggle")
    ok &= require(swift, "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN", "Swift second-backfill extra alpha gain knob")
    ok &= require(swift, "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN", "Swift second-backfill extra void gain knob")
    ok &= require(swift, "STICKERNEST_EXTERNAL_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_RESIDUAL_TARGET", "Swift second-backfill residual target toggle")
    ok &= require(swift, 'lowAlphaReadableRightCenterVoidChainSecondBackfillResidualTargetDefault = "0"', "Swift residual target default off")
    ok &= require(swift, 'lowAlphaReadableRightCenterVoidChainSecondBackfillDefault = "1"', "Swift second-backfill default")
    ok &= require(swift, 'environment["STICKERNEST_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE"] = lowAlphaReadable ? (lowAlphaReadableRightCenterVoidChainRelocateEnabled ? "1" : "0") : "0"', "Swift low-alpha-only chain env")
    ok &= require(swift, 'environment["STICKERNEST_LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL"] = lowAlphaReadable ? (lowAlphaReadableRightCenterVoidChainSecondBackfillEnabled ? "1" : "0") : "0"', "Swift low-alpha-only second-backfill env")
    ok &= require(swift, 'environment["STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN"]', "Swift passes chain min alpha gain")
    ok &= require(swift, 'environment["STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN"]', "Swift passes chain min void gain")
    ok &= require(swift, 'environment["STICKERNEST_RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT"]', "Swift passes chain node limit")
    ok &= require(swift, 'environment["STICKERNEST_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILLS"]', "Swift passes second-backfill cap")
    ok &= require(swift, 'environment["STICKERNEST_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN"]', "Swift passes second-backfill extra alpha gain")
    ok &= require(swift, 'environment["STICKERNEST_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN"]', "Swift passes second-backfill extra void gain")
    ok &= require(swift, 'environment["STICKERNEST_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL_RESIDUAL_TARGET"]', "Swift passes second-backfill residual target")
    ok &= require(swift, "rightCenterVoidChain=", "Swift begin log chain toggle")
    ok &= require(swift, "rightCenterVoidChainSecondBackfill=", "Swift begin log second-backfill toggle")
    ok &= require(swift, "rightCenterVoidChainMinAlphaGain=", "Swift begin log chain alpha gate")
    ok &= require(swift, "rightCenterVoidChainNodeLimit=", "Swift begin log chain node cap")
    ok &= require(swift, "version_low_alpha_readable_right_center_void_chain_relocate_changed", "Swift cache invalidation")
    ok &= require(swift, "version_low_alpha_readable_right_center_void_chain_carryforward_changed", "Swift carry-forward cache invalidation")
    ok &= require(swift, "version_low_alpha_readable_right_center_void_chain_second_backfill_changed", "Swift second-backfill cache invalidation")
    ok &= require(swift, "version_low_alpha_readable_right_center_void_chain_second_backfill_extra_gain_changed", "Swift second-backfill extra-gain cache invalidation")
    ok &= require(swift, "version_low_alpha_readable_right_center_void_chain_second_backfill_residual_target_changed", "Swift second-backfill residual-target cache invalidation")

    ok &= require(auto_nest, "LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE", "Python chain toggle")
    ok &= require(auto_nest, "LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL", "Python second-backfill toggle")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN", "Python chain min alpha gain")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_VOID_GAIN", "Python chain min void gain")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT", "Python chain node cap")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_BACKFILLS", "Python chain backfill cap")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILLS", "Python second-backfill cap")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN", "Python second-backfill extra alpha threshold")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN", "Python second-backfill extra void threshold")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET", "Python second-backfill residual target toggle")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED", "Python chain applied marker")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_APPLIED", "Python second-backfill applied marker")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_ALPHA_GAIN", "Python second-backfill extra alpha marker")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_VOID_GAIN", "Python second-backfill extra void marker")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_ALPHA_GAIN", "Python chain alpha gain marker")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_VOID_GAIN", "Python chain void gain marker")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED", "Python chain base applied marker")
    ok &= require(auto_nest, "RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED", "Python chain ever applied marker")
    ok &= require(auto_nest, "def refresh_right_center_void_chain_carryforward():", "Python carry-forward refresh helper")
    ok &= require(auto_nest, "right_center_void_chain_carryforward_from_base", "Python base carry-forward log")
    ok &= require(auto_nest, "def right_center_void_chain_relocate(pl, rounds=1):", "Python chain function")
    ok &= require(auto_nest, "LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE and LOW_ALPHA_READABLE_POSTPROCESS and MATERIAL_ALPHA_TOPUP and MANUAL_STAGGER", "Python chain low-alpha guard")
    ok &= require(auto_nest, 'base_stats["readable"]<N or base_stats["upside"]>0 or base_stats["sideways"]>0 or base_stats["hard"]>0', "Python base orientation guard")
    ok &= require(auto_nest, 'trial_stats["readable"]<N or trial_stats["upside"]>0 or trial_stats["sideways"]>0 or trial_stats["hard"]>0', "Python trial orientation guard")
    ok &= require(auto_nest, "layout_overlap_cells(trial)>0", "Python exact overlap guard")
    ok &= require(auto_nest, "trial_alpha<base_alpha+RIGHT_CENTER_VOID_CHAIN_RELOCATE_MIN_ALPHA_GAIN", "Python rejects no-alpha-gain moves")
    ok &= require(auto_nest, "if LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL and best_trial is not None:", "Python second-backfill guarded by existing best trial")
    ok &= require(auto_nest, "trial_audit_for_second=visual_audit_like(trial)", "Python second-backfill audits residual trial")
    ok &= require(auto_nest, "second_target_cells=right_center_void_targets(trial_audit_for_second", "Python second-backfill uses residual right-center targets")
    ok &= require(auto_nest, "second_target_cells+=band_void_fill_targets(trial_audit_for_second", "Python second-backfill can use residual band targets")
    ok &= require(auto_nest, "second_donors=band_void_fill_donors(current,trial_audit_for_second,second_target_cx,second_target_cy", "Python second-backfill donors come from residual target")
    ok &= require(auto_nest, "second_target_tile_gain=trial_audit[\"tile_fills\"][second_row*8+second_col]-base_audit[\"tile_fills\"][second_row*8+second_col]", "Python second-backfill scores residual target tile")
    ok &= require(auto_nest, "max(0.0,target_tile_gain,second_target_tile_gain)", "Python void gain considers residual target tile")
    ok &= require(auto_nest, "if second_backfill_used and best_two_step_alpha is not None:", "Python second-backfill compares against two-step trial")
    ok &= require(auto_nest, "second_extra_alpha_gain=trial_alpha-best_two_step_alpha", "Python second-backfill extra alpha calculation")
    ok &= require(auto_nest, "second_extra_void_gain=void_gain-best_two_step_void_gain", "Python second-backfill extra void calculation")
    ok &= require(auto_nest, "second_extra_alpha_gain<RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN and second_extra_void_gain<RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN", "Python rejects no-extra-gain second backfill")
    ok &= require(auto_nest, "def guided_options(layout, pos, fixed, target_cx, target_cy, factors, row_strength, limit, node_cap=None):", "Python guided options local node cap")
    ok &= require(auto_nest, "if node_count>=cap:\n                break\n            guided=place_guided", "Python guided options cap before guided placement")
    ok &= require(auto_nest, "second_node_cap=min(RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT,node_count+3500)", "Python second-backfill local node cap")
    ok &= require(auto_nest, "second_backfills=band_void_fill_backfills", "Python second-backfill candidate source")
    ok &= require(auto_nest, "right_center_void_chain_relocate accepted", "Python accepted debug log")
    ok &= require(auto_nest, "secondBackfill={RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_APPLIED}", "Python accepted debug second-backfill marker")
    ok &= require(auto_nest, "right_center_void_chain_relocate rejected", "Python rejected debug log")
    ok &= require(auto_nest, "rightCenterVoidChain={RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED}", "Python polish log chain marker")
    ok &= require(auto_nest, "rightCenterVoidChainEver={RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED}", "Python polish log cumulative chain marker")
    ok &= require(auto_nest, '"right_center_void_chain_relocate":LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_RELOCATE', "JSON chain toggle")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_APPLIED', "JSON chain applied")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_moves":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_MOVES)', "JSON chain moves")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_ALPHA_GAIN),4)', "JSON chain alpha gain")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_VOID_GAIN),4)', "JSON chain void gain")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_node_limit":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_NODE_LIMIT)', "JSON chain node cap")
    ok &= require(auto_nest, '"right_center_void_chain_second_backfill":LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL', "JSON second-backfill toggle")
    ok &= require(auto_nest, '"right_center_void_chain_second_backfill_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_APPLIED', "JSON second-backfill applied")
    ok &= require(auto_nest, '"right_center_void_chain_second_backfills":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILLS)', "JSON second-backfill cap")
    ok &= require(auto_nest, '"right_center_void_chain_second_backfill_min_extra_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_ALPHA_GAIN),4)', "JSON second-backfill extra alpha threshold")
    ok &= require(auto_nest, '"right_center_void_chain_second_backfill_min_extra_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_MIN_EXTRA_VOID_GAIN),4)', "JSON second-backfill extra void threshold")
    ok &= require(auto_nest, '"right_center_void_chain_second_backfill_residual_target":RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_RESIDUAL_TARGET', "JSON second-backfill residual target toggle")
    ok &= require(auto_nest, '"right_center_void_chain_second_backfill_extra_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_ALPHA_GAIN),4)', "JSON second-backfill extra alpha gain")
    ok &= require(auto_nest, '"right_center_void_chain_second_backfill_extra_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_SECOND_BACKFILL_EXTRA_VOID_GAIN),4)', "JSON second-backfill extra void gain")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_base_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_BASE_APPLIED', "JSON chain base applied")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_ever_applied":RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_APPLIED', "JSON chain ever applied")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_ever_moves":int(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_MOVES)', "JSON chain ever moves")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_ever_alpha_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_ALPHA_GAIN),4)', "JSON chain ever alpha gain")
    ok &= require(auto_nest, '"right_center_void_chain_relocate_ever_void_gain":round(float(RIGHT_CENTER_VOID_CHAIN_RELOCATE_EVER_VOID_GAIN),4)', "JSON chain ever void gain")

    ok &= require_order(
        auto_nest,
        "right_center_void_relocate(polish_candidate, rounds=1)",
        "right_center_void_chain_relocate(polish_candidate, rounds=1)",
        "chain after single right-center void pass",
    )
    ok &= require_order(
        auto_nest,
        "right_center_void_chain_relocate(polish_candidate, rounds=1)",
        "scale_transfer_repack(polish_candidate, rounds=1)",
        "chain before scale transfer",
    )
    ok &= require_order(
        auto_nest,
        "consider_chain_trial(trial,changed,row,col,donor_row,mover_move+backfill_move,False)",
        "if LOW_ALPHA_READABLE_RIGHT_CENTER_VOID_CHAIN_SECOND_BACKFILL and best_trial is not None:",
        "two-step trial before second backfill",
    )
    ok &= require_order(
        auto_nest,
        "trial_audit_for_second=visual_audit_like(trial)",
        "second_donors=band_void_fill_donors(current,trial_audit_for_second,second_target_cx,second_target_cy",
        "residual target audit before residual donors",
    )

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
