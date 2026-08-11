#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = AUTO_NEST.read_text()
    swift_source = SWIFT.read_text()

    required_python = {
        "STICKERNEST_ROW_PHASE_BASE_PROBE": "row-phase base probe env gate",
        "ROW_PHASE_BASE_PROBE": "row-phase base probe flag",
        "def row_phase_order_sets": "row-phase order generator",
        "row_phase_order_sets(base)": "human seeds include row-phase order sets",
        "if ROW_PHASE_BASE_PROBE": "row-phase is default-off gated",
        "\"row_phase_base_probe\"": "output json row-phase marker",
    }
    missing = [label for marker, label in required_python.items() if marker not in source]
    if missing:
        print("missing row-phase base probe markers: " + ", ".join(missing))
        return 1

    start = source.find("def row_phase_order_sets")
    end = source.find("\ndef human_seed_layouts", start)
    body = source[start:end]
    required_body = {
        "raw[i][1].sum()": "uses item alpha area for row balancing",
        "raw[i][1].shape[0]": "uses item height for row ordering",
        "raw[i][1].shape[1]": "uses item width for row ordering",
        "HUMAN_ROWS": "keeps existing row count",
        "HUMAN_COLS": "keeps existing column count",
        "snake": "keeps alternating row phase",
    }
    missing_body = [label for marker, label in required_body.items() if marker not in body]
    if missing_body:
        print("missing row-phase body markers: " + ", ".join(missing_body))
        return 1

    forbidden_body = {
        "make(": "must not build masks inside order generator",
        "place(": "must not place inside order generator",
        "compact(": "must not post-process inside order generator",
        "growfill(": "must not grow inside order generator",
        "layout_overlap_cells": "must not bypass normal exact replay guards",
        "nfp_probe": "must not call from-zero NFP probe",
    }
    forbidden = [label for marker, label in forbidden_body.items() if marker in body]
    if forbidden:
        print("forbidden row-phase body markers: " + ", ".join(forbidden))
        return 1

    required_swift = {
        "STICKERNEST_EXTERNAL_PRIMARY_ROW_PHASE_BASE_PROBE": "Swift row-phase env gate",
        "primaryRowPhaseBaseProbeDefault = \"0\"": "Swift row-phase diagnostic default-off",
        "primaryRowPhaseBaseProbeEnabled": "Swift row-phase enabled gate",
        "STICKERNEST_ROW_PHASE_BASE_PROBE": "Swift passes Python row-phase gate",
    }
    missing_swift = [label for marker, label in required_swift.items() if marker not in swift_source]
    if missing_swift:
        print("missing Swift row-phase base probe markers: " + ", ".join(missing_swift))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
