#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()

    required_python = {
        "STICKERNEST_SMALL_GROUP_MATERIAL_REPACK": "small-group material repack env gate",
        "SMALL_GROUP_MATERIAL_REPACK_APPLIED": "small-group applied flag",
        "SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT": "small-group node cap",
        "SMALL_GROUP_MATERIAL_REPACK_MIN_ACCEPT": "small-group minimum accept alpha",
        "SMALL_GROUP_MATERIAL_REPACK_MAX_CLUSTER_SIZE": "small-group cluster cap",
        "def small_group_material_repack": "small-group material repack pass",
        "def small_group_material_repack_targets": "small-group sparse target selector",
        "\"small_group_material_repack\"": "output json small-group marker",
        "\"small_group_material_repack_applied\"": "output json small-group applied marker",
        "\"small_group_material_repack_moves\"": "output json small-group move marker",
    }
    missing = [label for marker, label in required_python.items() if marker not in source]
    if missing:
        print("missing small-group material repack markers: " + ", ".join(missing))
        return 1

    structural_pos = source.find("candidate=structural_micro_grow(candidate, rounds=1)")
    group_pos = source.find("candidate=small_group_material_repack(candidate, rounds=1)")
    quality_pos = source.find("candidate_q=layout_quality(candidate)", group_pos)
    if min(structural_pos, group_pos, quality_pos) < 0:
        print("missing small-group ordering markers")
        return 1
    if not (structural_pos < group_pos < quality_pos):
        print("small-group material repack must run after structural micro grow and before candidate acceptance")
        return 1

    start = source.find("def small_group_material_repack")
    end = source.find("\ndef band_void_fill_targets", start)
    body = source[start:end]
    required_body = {
        "material_alpha_topup_alpha": "uses exported alpha metric",
        "build_occ_except_positions": "freezes non-local pieces",
        "layout_overlap_cells(trial)>0": "exact overlap rejection",
        "trial_stats[\"readable\"]<base_stats[\"readable\"]": "readable no-worse guard",
        "trial_stats[\"upside\"]>base_stats[\"upside\"]": "upside no-worse guard",
        "trial_stats[\"sideways\"]>base_stats[\"sideways\"]": "sideways no-worse guard",
        "trial_stats[\"hard\"]>base_stats[\"hard\"]": "hard no-worse guard",
        "trial_audit[\"size_cv\"]>base_cv+SMALL_GROUP_MATERIAL_REPACK_MAX_SIZE_CV_INCREASE": "size spread guard",
        "SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT": "node limit guard",
        "SMALL_GROUP_MATERIAL_REPACK_MAX_CLUSTER_SIZE": "cluster size guard",
        "SMALL_GROUP_MATERIAL_REPACK_APPLIED=True": "records accepted pass",
    }
    missing_body = [label for marker, label in required_body.items() if marker not in body]
    if missing_body:
        print("missing small-group material repack body markers: " + ", ".join(missing_body))
        return 1

    forbidden_body = {
        "local_angle_candidates(": "must not change angles inside small-group material repack",
        "compact(": "must not run broad compact inside small-group material repack",
        "growfill(": "must not run broad growfill inside small-group material repack",
        "void_relocate(": "must not call broad void relocation inside small-group material repack",
        "nfp_probe": "must not call from-zero NFP probe inside small-group material repack",
    }
    forbidden = [label for marker, label in forbidden_body.items() if marker in body]
    if forbidden:
        print("forbidden small-group material repack body markers: " + ", ".join(forbidden))
        return 1

    required_swift = {
        "STICKERNEST_EXTERNAL_PRIMARY_SMALL_GROUP_MATERIAL_REPACK": "Swift small-group env gate",
        "primarySmallGroupMaterialRepackEnabled": "Swift small-group enabled gate",
        "primarySmallGroupMaterialRepackMinAccept": "Swift small-group minimum accept",
        "primarySmallGroupMaterialRepackNodeLimit": "Swift small-group node limit",
        "primarySmallGroupMaterialRepackDefault = \"0\"": "Swift small-group diagnostic default-off",
        "STICKERNEST_SMALL_GROUP_MATERIAL_REPACK": "Swift passes Python small-group gate",
        "STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_MIN_ACCEPT": "Swift passes Python small-group min accept",
        "STICKERNEST_SMALL_GROUP_MATERIAL_REPACK_NODE_LIMIT": "Swift passes Python small-group node limit",
    }
    missing_swift = [label for marker, label in required_swift.items() if marker not in swift_source]
    if missing_swift:
        print("missing Swift small-group material repack markers: " + ", ".join(missing_swift))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
