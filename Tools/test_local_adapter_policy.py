#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()
    required_markers = {
        "STICKERNEST_LOCAL_ADAPTER": "local adapter env gate",
        "LOCAL_ADAPTER_APPLIED": "local adapter applied flag",
        "LOCAL_ADAPTER_NODE_LIMIT": "local adapter node cap",
        "LOCAL_ADAPTER_MIN_ACCEPT": "local adapter minimum alpha accept",
        "LOCAL_ADAPTER_FINE_OFFSETS": "local adapter fine offset scan",
        "STICKERNEST_LOCAL_ADAPTER_V2": "local adapter v2 env gate",
        "LOCAL_ADAPTER_V2_APPLIED": "local adapter v2 applied flag",
        "LOCAL_ADAPTER_MAX_CLUSTER_SIZE": "local adapter v2 cluster size cap",
        "LOCAL_ADAPTER_TARGET_MODE": "local adapter v2 target mode",
        "LOCAL_ADAPTER_V2_SCALE_FACTORS": "local adapter v2 scale factor set",
        "LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT": "local adapter rescue cluster cap",
        "LOCAL_ADAPTER_CHAIN_RESCUE_APPLIED": "local adapter chain rescue applied flag",
        "def local_adapter_repack": "local adapter pass",
        "def local_adapter_audit_void_tiles": "audit-derived void targets",
        "def layout_overlap_pairs": "exact layout overlap pair audit",
        "def layout_overlap_cells": "exact layout overlap audit",
        "def local_adapter_rescue_cluster_positions": "local adapter rescue cluster expansion",
        "blocker_counts": "local adapter rescue follows direct shift blockers",
        "owner_region": "local adapter rescue audits blocking owners",
        "def local_adapter_overlap_rescue": "local adapter overlap rescue",
        "positions=local_adapter_rescue_cluster_positions(trial, assigned)": "rescue can include direct blockers and local neighbors",
        "if len(positions)>=LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT": "rescue cluster hard cap",
        "LOCAL_ADAPTER_CHAIN_RESCUE_APPLIED=True": "records chain rescue acceptance",
        "candidate=local_adapter_repack(candidate, rounds=1)": "local adapter polish call",
        "if LOCAL_ADAPTER_V2:\n        candidate=local_adapter_repack(candidate, rounds=1, v2_pass=True)": "v2 second local adapter pass",
        "\"local_adapter\"": "output json local adapter marker",
        "\"local_adapter_applied\"": "output json local adapter applied marker",
        "\"local_adapter_v2\"": "output json local adapter v2 marker",
        "\"local_adapter_v2_applied\"": "output json local adapter v2 applied marker",
        "\"local_adapter_chain_rescue_applied\"": "output json local adapter chain rescue marker",
        "\"local_adapter_target_mode\"": "output json local adapter target mode marker",
        "\"local_adapter_min_gain\"": "output json local adapter min gain marker",
        "\"local_adapter_node_limit\"": "output json local adapter node limit marker",
        "\"local_adapter_moves\"": "output json local adapter moves marker",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing local adapter markers: " + ", ".join(missing))
        return 1

    multi_pos = source.find("candidate=multi_piece_material_topup(candidate, rounds=1)")
    adapter_pos = source.find("candidate=local_adapter_repack(candidate, rounds=1)")
    quality_pos = source.find("candidate_q=layout_quality(candidate)", adapter_pos)
    if multi_pos < 0 or adapter_pos < 0 or adapter_pos <= multi_pos:
        print("local adapter must run after multi-piece top-up")
        return 1
    if quality_pos < 0 or adapter_pos >= quality_pos:
        print("local adapter must run before candidate quality acceptance")
        return 1

    start = source.find("def local_adapter_repack")
    end = source.find("\ndef structural_micro_grow_relocation_options", start)
    body = source[start:end]
    required_body_markers = {
        "material_alpha_topup_alpha": "uses exported-alpha metric",
        "build_occ_except_positions": "freezes non-local pieces",
        "trial_stats[\"readable\"]<base_stats[\"readable\"]": "readable no-worse guard",
        "if layout_overlap_cells(trial)>0": "exact overlap no-accept guard",
        "trial=local_adapter_overlap_rescue(trial, assigned)": "tries bounded overlap rescue before rejecting",
        "trial_stats[\"upside\"]>base_stats[\"upside\"]": "upside no-worse guard",
        "trial_stats[\"sideways\"]>base_stats[\"sideways\"]": "sideways no-worse guard",
        "trial_stats[\"hard\"]>base_stats[\"hard\"]": "hard no-worse guard",
        "trial_audit[\"size_cv\"]>base_cv+LOCAL_ADAPTER_MAX_SIZE_CV_INCREASE": "size spread guard",
        "node_count>LOCAL_ADAPTER_NODE_LIMIT": "node limit guard",
        "for dx in LOCAL_ADAPTER_FINE_OFFSETS": "fine x offset scan",
        "candidates.add((x+dx,y+dy))": "current-neighborhood fine candidates",
        "cluster_sizes=(3,4)": "v2 can try bounded 4-piece local chains",
        "local_adapter_audit_void_tiles(pl, base_audit)": "v2 can derive target tiles from visual audit",
        "if not LOCAL_ADAPTER_V2 and cluster_size>3": "v2 cluster gate",
        "scale_factors=LOCAL_ADAPTER_V2_SCALE_FACTORS if (LOCAL_ADAPTER_V2 and cluster_size>3) else LOCAL_ADAPTER_SCALE_FACTORS": "v2 uses its own bounded scale candidates",
        "LOCAL_ADAPTER_V2_APPLIED=LOCAL_ADAPTER_V2_APPLIED or (LOCAL_ADAPTER_V2 and (v2_pass or best_cluster_size>3))": "v2 applied marker covers second pass",
        "LOCAL_ADAPTER_MOVES+=best_move_count": "local adapter move count accumulates across v2 second pass",
    }
    missing_body = [label for marker, label in required_body_markers.items() if marker not in body]
    if missing_body:
        print("missing local adapter body markers: " + ", ".join(missing_body))
        return 1

    forbidden_body_markers = {
        "local_angle_candidates(": "must not change angles inside local adapter",
        "compact(": "must not run broad compact inside local adapter",
        "growfill(": "must not run broad growfill inside local adapter",
        "void_relocate(": "must not call broad void relocation inside local adapter",
        "nfp_probe": "must not call from-zero NFP probe inside local adapter",
    }
    forbidden = [label for marker, label in forbidden_body_markers.items() if marker in body]
    if forbidden:
        print("forbidden local adapter body markers: " + ", ".join(forbidden))
        return 1

    required_swift_markers = {
        "STICKERNEST_EXTERNAL_PRIMARY_LOCAL_ADAPTER": "Swift local adapter env gate",
        "STICKERNEST_EXTERNAL_PRIMARY_LOCAL_ADAPTER_V2": "Swift local adapter v2 env gate",
        "primaryLocalAdapterEnabled": "Swift local adapter enabled gate",
        "primaryLocalAdapterV2Enabled": "Swift local adapter v2 enabled gate",
        "primaryLocalAdapterMinAccept": "Swift local adapter min accept",
        "0.5532": "Swift default local adapter accept alpha 55.32%",
        "0.5536": "Swift default local adapter v2 accept alpha 55.36%",
        "primaryLocalAdapterNodeLimit": "Swift local adapter node limit",
        "primaryLocalAdapterMaxClusterSize": "Swift local adapter cluster cap",
        "STICKERNEST_EXTERNAL_PRIMARY_LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT": "Swift local adapter rescue cluster cap env",
        "primaryLocalAdapterRescueClusterLimit": "Swift local adapter rescue cluster cap",
        "STICKERNEST_LOCAL_ADAPTER": "Swift passes Python local adapter gate",
        "STICKERNEST_LOCAL_ADAPTER_V2": "Swift passes Python local adapter v2 gate",
        "STICKERNEST_LOCAL_ADAPTER_MAX_CLUSTER_SIZE": "Swift passes Python local adapter cluster cap",
        "STICKERNEST_LOCAL_ADAPTER_RESCUE_CLUSTER_LIMIT": "Swift passes Python local adapter rescue cluster cap",
        "STICKERNEST_LOCAL_ADAPTER_TARGET_MODE": "Swift passes Python local adapter target mode",
        "STICKERNEST_LOCAL_ADAPTER_MIN_ACCEPT": "Swift passes Python local adapter min accept",
        "STICKERNEST_LOCAL_ADAPTER_NODE_LIMIT": "Swift passes Python local adapter node limit",
        "version_local_adapter_v2_changed": "cache invalidation key",
        "version_local_adapter_chain_rescue_changed": "cache invalidation key for chain rescue memory guard",
    }
    missing_swift = [label for marker, label in required_swift_markers.items() if marker not in swift_source]
    if missing_swift:
        print("missing Swift local adapter markers: " + ", ".join(missing_swift))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
