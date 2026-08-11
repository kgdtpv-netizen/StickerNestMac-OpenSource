#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()
    required_markers = {
        "STICKERNEST_MULTI_PIECE_TOPUP": "multi-piece top-up env gate",
        "STICKERNEST_MULTI_PIECE_TOPUP_NODE_LIMIT": "multi-piece top-up node limit",
        "MULTI_PIECE_TOPUP_APPLIED": "multi-piece top-up applied flag",
        "def multi_piece_material_topup": "multi-piece material top-up pass",
        "candidate_exported_alpha=material_alpha_topup_alpha(candidate)": "outer exported-alpha candidate metric",
        "best_exported_alpha=material_alpha_topup_alpha(bestpl)": "outer exported-alpha best metric",
        "material_alpha_topup_alpha": "uses exported alpha metric",
        "\"multi_piece_topup\"": "output json top-up marker",
        "\"multi_piece_topup_applied\"": "output json applied marker",
        "\"multi_piece_topup_moves\"": "output json move marker",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing multi-piece void-fill markers: " + ", ".join(missing))
        return 1

    material_pos = source.find("candidate=material_alpha_topup(candidate, rounds=1)")
    multi_pos = source.find("candidate=multi_piece_material_topup(candidate, rounds=1)")
    if material_pos < 0 or multi_pos < 0 or multi_pos <= material_pos:
        print("multi-piece top-up must run after material_alpha_topup")
        return 1
    quality_pos = source.find("candidate_q=layout_quality(candidate)", multi_pos)
    if quality_pos < 0 or multi_pos >= quality_pos:
        print("multi-piece top-up must run before candidate quality acceptance")
        return 1

    start = source.find("def multi_piece_material_topup")
    end = source.find("\ndef local_adapter_target_tiles", start)
    body = source[start:end]
    required_body_markers = {
        "node_count": "bounded node counter",
        "MULTI_PIECE_TOPUP_NODE_LIMIT": "node limit guard",
        "mask_overlap_blockers": "direct blocker detection",
        "trial_stats[\"upside\"]>base_stats[\"upside\"]": "upside no-worse guard",
        "trial_stats[\"sideways\"]>base_stats[\"sideways\"]": "sideways no-worse guard",
        "trial_stats[\"hard\"]>base_stats[\"hard\"]": "hard no-worse guard",
    }
    missing_body = [label for marker, label in required_body_markers.items() if marker not in body]
    if missing_body:
        print("missing multi-piece body markers: " + ", ".join(missing_body))
        return 1
    forbidden_body_markers = {
        "local_angle_candidates(": "must not change angles inside multi-piece top-up",
        "compact(": "must not run broad compact inside multi-piece top-up",
        "growfill(": "must not run broad growfill inside multi-piece top-up",
        "void_relocate(": "must not call broad void relocation inside multi-piece top-up",
    }
    forbidden = [label for marker, label in forbidden_body_markers.items() if marker in body]
    if forbidden:
        print("forbidden multi-piece body markers: " + ", ".join(forbidden))
        return 1
    required_swift_markers = {
        "STICKERNEST_EXTERNAL_PRIMARY_MULTI_PIECE_TOPUP": "Swift multi-piece top-up env gate",
        "primaryMultiPieceTopupTargetAlpha": "Swift multi-piece target alpha",
        "0.5530": "Swift default multi-piece target alpha 55.30%",
        "0.5527": "Swift default multi-piece accept alpha 55.27%",
        "primaryMultiPieceTopupEnabled": "Swift multi-piece enabled gate",
        "manualStaggerExternalMode ? 2 : 1": "Swift default multi-piece max moves",
        "manualStaggerExternalMode ? 2 : 1": "Swift default multi-piece max blockers",
        "manualStaggerExternalMode ? 28 : 16": "Swift default multi-piece relocate radius",
        "manualStaggerExternalMode ? 10 : 4": "Swift default multi-piece option count",
        "manualStaggerExternalMode ? 8 : 3": "Swift default multi-piece target count",
        "manualStaggerExternalMode ? 8000 : 1000": "Swift default multi-piece node limit",
        "STICKERNEST_MULTI_PIECE_TOPUP": "Swift passes Python multi-piece gate",
        "STICKERNEST_MULTI_PIECE_TOPUP_TARGET": "Swift passes Python multi-piece target",
        "STICKERNEST_MULTI_PIECE_TOPUP_NODE_LIMIT": "Swift passes Python multi-piece node limit",
        "version_multi_piece_topup_chain_changed": "cache invalidation key",
    }
    missing_swift = [label for marker, label in required_swift_markers.items() if marker not in swift_source]
    if missing_swift:
        print("missing Swift multi-piece markers: " + ", ".join(missing_swift))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
