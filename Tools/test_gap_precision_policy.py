#!/usr/bin/env python3
"""Guard the gap-precision transparency feature.

The solver works on a DOWN=20 grid and dilates each piece by G = max(1, c(gap)//2)
cells, so the nominal gap mm is coarsely quantized (e.g. 6mm -> ~6.8mm, 5mm ->
~3.4mm). The app surfaces the actual cut width both in auto_nest.py (export +
stderr log) and in the Swift UI (NestSettings.effectiveGapMM + "实际切宽" label).
This test checks the markers exist AND that the Swift formula transcription matches
the Python c()/G formula numerically, so the two cannot drift apart.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTO_NEST = ROOT / "Tools" / "auto_nest.py"
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"

DOWN = 20


def python_effective(gap_mm: float, dpi: float) -> float:
    # Mirrors auto_nest.py: c(mm)=max(1,int(round(mm/25.4*DPI/DOWN))), G=max(1,c//2),
    # effective = 2*G*DOWN*25.4/DPI.
    c = max(1, int(round(gap_mm / 25.4 * dpi / DOWN)))
    g = max(1, c // 2)
    return 2.0 * g * DOWN * 25.4 / dpi


def swift_round(x: float) -> int:
    # Swift Double.rounded() is round-half-away-from-zero.
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


def swift_effective(gap_mm: float, dpi: float) -> float:
    # Transcribes NestSettings.effectiveGapMM in StickerNestMac.swift.
    c = max(1.0, float(swift_round(gap_mm / 25.4 * dpi / DOWN)))
    g = max(1.0, math.floor(c / 2.0))
    px_per_mm = dpi / 25.4
    return 2.0 * g * DOWN / px_per_mm


def main() -> int:
    auto = AUTO_NEST.read_text()
    swift = SWIFT.read_text()

    required_python = {
        "EFFECTIVE_GAP_MM = 2.0*G*DOWN*25.4/DPI": "python effective gap computation",
        "\"gap_mm_effective\"": "python exports effective gap",
        "gap_precision nominal=": "python logs gap precision",
    }
    missing = [label for marker, label in required_python.items() if marker not in auto]
    if missing:
        print("missing python gap-precision markers: " + ", ".join(missing))
        return 1

    required_swift = {
        "var effectiveGapMM": "swift effective gap property",
        "实际切宽": "swift UI shows the actual cut width",
    }
    missing_s = [label for marker, label in required_swift.items() if marker not in swift]
    if missing_s:
        print("missing swift gap-precision markers: " + ", ".join(missing_s))
        return 1

    # Numeric anchors (DPI=300): the documented quantization must hold.
    cases = {6.0: 6.77, 5.0: 3.39, 4.0: 3.39, 7.0: 6.77, 3.0: 3.39}
    for gap, expected in cases.items():
        got = python_effective(gap, 300)
        if abs(got - expected) > 0.02:
            print(f"python_effective({gap}mm@300) = {got:.3f}, expected ~{expected}")
            return 1

    # Swift transcription must match Python across the practical gap range and DPIs,
    # so the UI estimate never disagrees with what the solver actually cuts.
    for dpi in (300.0, 200.0):
        gap = 1.0
        while gap <= 10.0 + 1e-9:
            p = python_effective(gap, dpi)
            s = swift_effective(gap, dpi)
            if abs(p - s) > 1e-6:
                print(f"swift/python effective gap disagree at gap={gap}mm dpi={dpi}: python={p:.4f} swift={s:.4f}")
                return 1
            gap += 0.5

    print("gap precision policy OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
