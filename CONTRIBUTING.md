# Contributing

Thanks for helping improve StickerNestMac.

## Before opening a change

1. Open an issue describing the bug, experiment, or proposed behavior.
2. Keep changes focused and explain the print-safety impact.
3. Do not commit customer files, production QR codes, personal paths, internal logs, production-derived policy JSON, or third-party artwork without explicit redistribution rights.
4. Add or update a policy test when behavior changes.

## Local checks

```bash
python3 -m compileall -q Tools
python3 Tools/test_external_memory_guard_policy.py
python3 Tools/test_gap_precision_policy.py
python3 Tools/test_route_selector_policy.py
python3 Tools/test_ui_optimization_task_guard.py
zsh build.zsh
```

For solver changes, describe the input assumptions, measurement method, and any trade-off between material use, readability, gap safety, and runtime.

## Pull requests

- Use a clear title and summary.
- State the macOS and Python versions tested.
- Include only synthetic or redistributable fixtures.
- Never present benchmark gains without the comparison method and safety constraints.

Contributions are licensed under the repository's MIT License.
