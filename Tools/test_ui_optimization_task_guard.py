#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def section(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    finish = source.index(end, begin)
    return source[begin:finish]


def main() -> int:
    source = SWIFT.read_text()
    refine = section(source, "func refineCurrentLayout()", "func globalV2Nest()")
    required = {
        "activeOptimizationTask?.cancel()": "refine cancels previous task",
        "optimizationRunID += 1": "refine advances run id",
        "let runID = optimizationRunID": "refine captures run id",
        "activeOptimizationTask = Task.detached": "refine registers cancellable task",
        "runID: runID": "refine progress is run guarded",
        "shouldCancel: { Task.isCancelled }": "refine passes cancellation into multi strategy",
        "guard runID == self.optimizationRunID else { return }": "refine final write is run guarded",
        "self.activeOptimizationTask = nil": "refine clears active task only on current run",
    }
    missing = [label for marker, label in required.items() if marker not in refine]
    if missing:
        print("missing UI optimization task guards: " + ", ".join(missing))
        return 1

    multi_strategy = section(source, "static func multiStrategyVisualOptimize(", "static func spreadToFullHeight(")
    cancel_required = {
        "shouldCancel: @escaping @Sendable () -> Bool": "multi strategy accepts a cancellation callback",
        "multi_strategy_cancelled": "multi strategy logs cancellation",
        "shouldCancel()": "multi strategy checks cancellation between expensive passes",
    }
    missing = [label for marker, label in cancel_required.items() if marker not in multi_strategy]
    if missing:
        print("missing multi strategy cancellation guards: " + ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
