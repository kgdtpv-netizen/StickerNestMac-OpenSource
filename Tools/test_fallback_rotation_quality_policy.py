#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required = {
        "STICKERNEST_EXTERNAL_FALLBACK_READABLE_VARIANTS": "fallback readable variants env gate",
        "fallbackReadableVariantsEnabled": "fallback readable variants enabled flag",
        "fallbackReadableNoRotateMinDeltaMM": "fallback readable lower-target threshold",
        "STICKERNEST_EXTERNAL_FALLBACK_READABLE_NO_ROTATE_MIN_DELTA_MM": "fallback readable min delta env",
        "external_auto_nest_readable_variant_begin": "readable variant attempt log",
        "manualRotate": "attempt logs include manual rotate state",
        "external_auto_nest_candidate_best": "keeps normal best-candidate flow",
        "readableVariant": "candidate records readable variant",
        "version_fallback_readable_variants_changed": "cache invalidation key",
    }
    missing = [label for marker, label in required.items() if marker not in source]
    if missing:
        print("missing fallback readable policy markers: " + ", ".join(missing))
        return 1

    no_rotate_env_pos = source.find('environment["STICKERNEST_MANUAL_STAGGER_ROTATE"] = "0"')
    if no_rotate_env_pos < 0:
        print("missing no-rotate Python env override")
        return 1

    begin_pos = source.find("external_auto_nest_attempt_begin")
    variant_pos = source.find("external_auto_nest_readable_variant_begin")
    run_pos = source.find("try process.run()", begin_pos)
    if min(begin_pos, variant_pos, run_pos) < 0:
        print("missing readable variant process ordering markers")
        return 1
    if not (begin_pos < variant_pos < run_pos):
        print("readable variant decision should be logged before running the external process")
        return 1

    output_marker = "layout-\\(attemptIndex)-seed\\(seed)-\\(targetCandidate.outputNameToken)"
    if output_marker not in source or "rotate0" not in source:
        print("readable variant output path must be distinct from normal candidate output")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
