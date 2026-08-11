#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()

    required_python = {
        "STICKERNEST_SCALE_TRANSFER": "scale transfer env gate",
        "SCALE_TRANSFER_APPLIED": "scale transfer applied flag",
        "SCALE_TRANSFER_MIN_ACCEPT": "scale transfer minimum accept",
        "SCALE_TRANSFER_NODE_LIMIT": "scale transfer node limit",
        "def scale_transfer_repack": "scale transfer pass",
        "\"scale_transfer\"": "output json scale transfer marker",
        "\"scale_transfer_applied\"": "output json scale transfer applied marker",
        "\"scale_transfer_moves\"": "output json scale transfer moves marker",
    }
    missing = [label for marker, label in required_python.items() if marker not in source]
    if missing:
        print("missing scale transfer markers: " + ", ".join(missing))
        return 1

    structural_pos = source.find("candidate=structural_micro_grow(candidate, rounds=1)")
    transfer_pos = source.find("candidate=scale_transfer_repack(candidate, rounds=1)")
    small_group_pos = source.find("candidate=small_group_material_repack(candidate, rounds=1)")
    quality_pos = source.find("candidate_q=layout_quality(candidate)", structural_pos)
    if min(structural_pos, transfer_pos, small_group_pos, quality_pos) < 0:
        print("missing scale transfer ordering markers")
        return 1
    if not (structural_pos < transfer_pos < small_group_pos < quality_pos):
        print("scale transfer must run after structural micro grow and before small-group diagnostic/acceptance")
        return 1

    start = source.find("def scale_transfer_repack")
    end = source.find("\ndef small_group_material_repack_targets", start)
    body = source[start:end]
    required_body = {
        "shrink_factors": "uses bounded shrink factors",
        "grow_factors": "uses bounded grow factors",
        "layout_overlap_cells(trial)>0": "exact overlap rejection",
        "orientation_stats": "checks orientation guards",
        "trial_audit[\"size_cv\"]": "size spread guard",
        "SCALE_TRANSFER_NODE_LIMIT": "node limit guard",
        "SCALE_TRANSFER_MIN_ACCEPT": "minimum alpha accept guard",
        "SCALE_TRANSFER_APPLIED=True": "records accepted pass",
        "SCALE_TRANSFER_MOVES=2": "records pair move count",
    }
    missing_body = [label for marker, label in required_body.items() if marker not in body]
    if missing_body:
        print("missing scale transfer body markers: " + ", ".join(missing_body))
        return 1

    forbidden_body = {
        "local_angle_candidates(": "must not change angles inside scale transfer",
        "compact(": "must not run broad compact inside scale transfer",
        "growfill(": "must not run broad growfill inside scale transfer",
        "void_relocate(": "must not call broad void relocation inside scale transfer",
    }
    forbidden = [label for marker, label in forbidden_body.items() if marker in body]
    if forbidden:
        print("forbidden scale transfer body markers: " + ", ".join(forbidden))
        return 1

    required_swift = {
        "STICKERNEST_EXTERNAL_PRIMARY_SCALE_TRANSFER": "Swift scale transfer env gate",
        "primaryScaleTransferEnabled": "Swift scale transfer enabled gate",
        "primaryScaleTransferMinAccept": "Swift scale transfer minimum accept",
        "primaryScaleTransferNodeLimit": "Swift scale transfer node limit",
        "STICKERNEST_SCALE_TRANSFER": "Swift passes Python scale transfer gate",
        "STICKERNEST_SCALE_TRANSFER_MIN_ACCEPT": "Swift passes Python scale transfer minimum accept",
        "STICKERNEST_SCALE_TRANSFER_NODE_LIMIT": "Swift passes Python scale transfer node limit",
        "0.5545": "Swift default scale transfer accept alpha 55.45%",
        "version_scale_transfer_changed": "cache invalidation key",
    }
    missing_swift = [label for marker, label in required_swift.items() if marker not in swift_source]
    if missing_swift:
        print("missing Swift scale transfer markers: " + ", ".join(missing_swift))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
