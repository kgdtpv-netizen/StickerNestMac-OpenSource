#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWIFT = ROOT / "Sources" / "StickerNestMac.swift"


def main() -> int:
    source = SWIFT.read_text()
    required_markers = {
        "STICKERNEST_EXTERNAL_PROCESS_MEMORY_LIMIT_MB": "external process memory limit env",
        "externalProcessMemoryLimitMB": "configured external memory limit",
        "externalProcessRSSMB": "external process RSS sampler",
        "/bin/ps": "RSS sampler uses ps",
        "external_auto_nest_memory_guard_terminated": "memory guard termination log",
        "rssMB": "RSS value logged",
        "limitMB": "memory limit logged",
        "内存异常": "user-facing memory safety status",
        "func hardTerminate": "SIGTERM->SIGKILL escalation helper",
        "SIGKILL": "force-kill escalation signal",
        "external_auto_nest_process_sigkill_escalated": "sigkill escalation log",
        "Self.hardTerminate(process)": "memory guard uses the escalating terminate",
        "timeIntervalSince(lastMemoryCheck) >= 0.34": "faster (<0.5s) memory poll to bound overshoot",
    }
    missing = [label for marker, label in required_markers.items() if marker not in source]
    if missing:
        print("missing external memory guard markers: " + ", ".join(missing))
        return 1

    attempt_pos = source.find("external_auto_nest_attempt_begin")
    run_pos = source.find("try process.run()", attempt_pos)
    guard_pos = source.find("external_auto_nest_memory_guard_terminated", run_pos)
    sleep_pos = source.find("Thread.sleep(forTimeInterval: 0.2)", run_pos)
    elapsed_pos = source.find("let elapsed = Date().timeIntervalSince(started)", sleep_pos)
    if attempt_pos < 0 or run_pos < 0 or guard_pos < 0 or sleep_pos < 0 or elapsed_pos < 0:
        print("could not locate external process loop markers")
        return 1
    if not (run_pos < guard_pos < elapsed_pos):
        print("memory guard must run while the external process is alive")
        return 1
    if not (guard_pos < sleep_pos):
        print("memory guard should check before sleeping in the process loop")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
