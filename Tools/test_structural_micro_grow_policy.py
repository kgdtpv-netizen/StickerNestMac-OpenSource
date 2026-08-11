#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()

    required_python = {
        "STICKERNEST_STRUCTURAL_MICRO_GROW": "structural micro grow env gate",
        "STRUCTURAL_MICRO_GROW_APPLIED": "structural micro grow applied flag",
        "STRUCTURAL_MICRO_GROW_MIN_ACCEPT": "structural micro grow minimum accept",
        "STRUCTURAL_MICRO_GROW_MAX_BLOCKERS": "structural micro grow blocker cap",
        "def structural_micro_grow": "structural micro grow pass",
        "def structural_micro_grow_relocation_options": "structural micro grow blocker relocation",
        "mask_overlap_blockers(current,pos,nx,ny,m)": "uses exact grow blocker detection",
        "\"structural_micro_grow\"": "output json structural micro grow marker",
        "\"structural_micro_grow_applied\"": "output json structural micro grow applied marker",
        "\"structural_micro_grow_moves\"": "output json structural micro grow move count marker",
    }
    missing = [label for marker, label in required_python.items() if marker not in source]
    if missing:
        print("missing structural micro grow markers: " + ", ".join(missing))
        return 1

    multi_pos = source.find("candidate=multi_piece_material_topup(candidate, rounds=1)")
    adapter_pos = source.find("candidate=local_adapter_repack(candidate, rounds=1)")
    grow_pos = source.find("candidate=structural_micro_grow(candidate, rounds=1)")
    quality_pos = source.find("candidate_q=layout_quality(candidate)", adapter_pos)
    if min(multi_pos, adapter_pos, grow_pos, quality_pos) < 0:
        print("missing structural micro grow ordering markers")
        return 1
    if not (multi_pos < adapter_pos < grow_pos < quality_pos):
        print("structural micro grow must run after local adapter and before candidate acceptance")
        return 1

    start = source.find("def structural_micro_grow")
    end = source.find("\ndef scale_transfer_repack", start)
    body = source[start:end]
    required_body = {
        "material_alpha_topup_alpha": "uses exported alpha metric",
        "orientation_stats": "checks orientation guards",
        "layout_overlap_cells(trial)>0": "exact overlap rejection",
        "trial_audit[\"size_cv\"]": "size spread guard",
        "STRUCTURAL_MICRO_GROW_NODE_LIMIT": "node limit guard",
        "STRUCTURAL_MICRO_GROW_MAX_BLOCKERS": "blocker cap guard",
        "STRUCTURAL_MICRO_GROW_CLOSE_RELOCATE_RADIUS": "close blocker relocation guard",
        "SW*0.20<cx<SW*0.72": "lower structural blank target priority",
        "STRUCTURAL_MICRO_GROW_APPLIED=True": "records accepted pass",
    }
    missing_body = [label for marker, label in required_body.items() if marker not in body]
    if missing_body:
        print("missing structural micro grow body markers: " + ", ".join(missing_body))
        return 1

    forbidden_body = {
        "local_angle_candidates(": "must not change angles inside structural micro grow",
        "compact(": "must not run broad compact inside structural micro grow",
        "growfill(": "must not run broad growfill inside structural micro grow",
        "void_relocate(": "must not call broad void relocation inside structural micro grow",
    }
    forbidden = [label for marker, label in forbidden_body.items() if marker in body]
    if forbidden:
        print("forbidden structural micro grow body markers: " + ", ".join(forbidden))
        return 1

    required_swift = {
        "STICKERNEST_EXTERNAL_PRIMARY_STRUCTURAL_MICRO_GROW": "Swift structural micro grow env gate",
        "primaryStructuralMicroGrowEnabled": "Swift structural micro grow enabled gate",
        "primaryStructuralMicroGrowMinAccept": "Swift structural micro grow minimum accept",
        "primaryStructuralMicroGrowMaxBlockers": "Swift structural micro grow blocker cap",
        "STICKERNEST_STRUCTURAL_MICRO_GROW": "Swift passes Python structural micro grow gate",
        "STICKERNEST_STRUCTURAL_MICRO_GROW_MIN_ACCEPT": "Swift passes Python structural micro grow minimum accept",
        "STICKERNEST_STRUCTURAL_MICRO_GROW_MAX_BLOCKERS": "Swift passes Python structural micro grow blocker cap",
        "0.5540": "Swift default structural micro grow blocker-2 accept alpha 55.40%",
        "version_structural_micro_grow_blocker2_changed": "cache invalidation key",
    }
    missing_swift = [label for marker, label in required_swift.items() if marker not in swift_source]
    if missing_swift:
        print("missing Swift structural micro grow markers: " + ", ".join(missing_swift))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
