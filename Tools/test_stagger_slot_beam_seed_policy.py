#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()

    required_python = {
        "STICKERNEST_STAGGER_SLOT_BEAM_SEED": "stagger slot beam env gate",
        "STAGGER_SLOT_BEAM_SEED_NODE_LIMIT": "stagger slot beam node cap",
        "STAGGER_SLOT_BEAM_SEED_WIDTH": "stagger slot beam width cap",
        "def stagger_slot_beam_seed_layouts": "stagger slot beam generator",
        "stagger_templates(": "uses existing stagger templates",
        "manual_rotation_seed(": "uses existing manual rotation pattern",
        "place_guided(": "uses guided placement",
        "layout_quality(": "scores generated layouts",
        "orientation_hard_reject(": "keeps orientation hard reject",
        "\"stagger_slot_beam_seed\"": "output json stagger slot marker",
    }
    missing = [label for marker, label in required_python.items() if marker not in source]
    if missing:
        print("missing stagger slot beam markers: " + ", ".join(missing))
        return 1

    human_pos = source.find("for label,order,rots,scs,pl in human_seed_layouts():")
    beam_pos = source.find("for label,order,rots,scs,pl in stagger_slot_beam_seed_layouts():")
    loop_pos = source.find("while time.time()-t0<SECS:")
    if min(human_pos, beam_pos, loop_pos) < 0:
        print("missing stagger slot beam ordering markers")
        return 1
    if not (human_pos < beam_pos < loop_pos):
        print("stagger slot beam must run after human seeds and before random main loop")
        return 1

    start = source.find("def stagger_slot_beam_seed_layouts")
    end = source.find("\nbest=-1e9", start)
    body = source[start:end]
    required_body = {
        "STAGGER_SLOT_BEAM_SEED": "default-off function gate",
        "STAGGER_SLOT_BEAM_SEED_NODE_LIMIT": "node limit guard",
        "STAGGER_SLOT_BEAM_SEED_WIDTH": "beam width guard",
        "STAGGER_SLOT_BEAM_SEED_CANDIDATES": "candidate cap guard",
        "len(pl)==N": "only returns complete layouts",
        "orientation_hard_reject(pl)": "rejects unsafe orientation",
    }
    missing_body = [label for marker, label in required_body.items() if marker not in body]
    if missing_body:
        print("missing stagger slot beam body markers: " + ", ".join(missing_body))
        return 1

    forbidden_body = {
        "nfp_probe": "must not call from-zero NFP probe",
        "small_group_material_repack": "must not use post-structural small-group repack",
        "structural_micro_grow": "must not use post-structural growth inside base generator",
        "void_relocate": "must not call void relocation inside base generator",
        "growfill": "must not grow inside base generator",
        "compact": "must not compact inside base generator",
        "recover_multi_missing": "must not run broad recovery inside base generator",
    }
    forbidden = [label for marker, label in forbidden_body.items() if marker in body]
    if forbidden:
        print("forbidden stagger slot beam body markers: " + ", ".join(forbidden))
        return 1

    required_swift = {
        "STICKERNEST_EXTERNAL_PRIMARY_STAGGER_SLOT_BEAM_SEED": "Swift stagger slot beam env gate",
        "primaryStaggerSlotBeamSeedDefault = \"0\"": "Swift stagger slot beam diagnostic default-off",
        "primaryStaggerSlotBeamSeedEnabled": "Swift stagger slot beam enabled gate",
        "STICKERNEST_STAGGER_SLOT_BEAM_SEED": "Swift passes Python stagger slot gate",
    }
    missing_swift = [label for marker, label in required_swift.items() if marker not in swift_source]
    if missing_swift:
        print("missing Swift stagger slot beam markers: " + ", ".join(missing_swift))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
