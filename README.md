# StickerNestMac

A local-first macOS research tool for arranging irregular transparent sticker artwork on print sheets while preserving cut clearance, readable orientation, and layout safety.

> Status: early open-source release. This repository is a sanitized source release; private production datasets, QR mappings, and third-party artwork are intentionally not included.

[简体中文说明](README.zh-CN.md)

## What it does

- Imports transparent artwork and computes shape-aware placements.
- Uses a native SwiftUI front end with a Python/OpenCV nesting engine.
- Checks bounds, overlap, readable orientation, and effective cut gap.
- Guards external solver memory and escalates termination for stuck processes.
- Runs locally and contains no network or telemetry code.

The default solver profile targets an A2-like 420 × 594 mm sheet. Results still require a real print-and-cut safety check before production use.

## Requirements

- Apple Silicon Mac
- macOS 14 or newer
- Xcode Command Line Tools with Swift
- Python 3.11 or newer
- NumPy and OpenCV

## Build and run

```bash
xcode-select --install
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
zsh build.zsh
STICKERNEST_PYTHON="$PWD/.venv/bin/python3" open "build/异形贴纸排版.app"
```

The app checks `STICKERNEST_PYTHON` first, then the project `.venv`, Homebrew Python, and finally `/usr/bin/python3`.
An optional PSD template can be supplied with `STICKERNEST_TEMPLATE_PSD=/absolute/path/to/template.psd`.

## Tests

```bash
for test_file in Tools/test_*.py; do
  python3 "$test_file" || exit 1
done
```

CI also compiles all Python utilities and builds the macOS app.

## Repository layout

- `Sources/StickerNestMac.swift` — SwiftUI application and native layout safety logic.
- `Tools/auto_nest.py` — shape-aware solver.
- `Tools/test_*.py` — policy and regression checks.
- `Resources/` — documents the boundary for local, non-versioned policy data.
- `docs/ARCHITECTURE.md` — component and data-flow overview.

## Data and asset policy

No celebrity images, customer artwork, production QR codes, local file manifests, private benchmark history, or production-derived policy JSON is included. The public build copies only its two allowlisted runtime Python scripts; it does not copy `Resources/` wholesale. Optional profiles learned locally stay in the user's Application Support directory and outside Git. Contributors must only add data and artwork they are authorized to redistribute. See [NOTICE.md](NOTICE.md).

## Current limitations

- The Swift application is still a large single source file and needs modularization.
- The checked-in build script currently targets Apple Silicon.
- There is no notarized binary release yet.
- The public solver uses generic built-in defaults; production-derived manual layout and stagger policies are deliberately excluded.
- This is not a substitute for cutter calibration or a production proof.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). By contributing, you agree that your contribution is provided under the MIT License.

## License

MIT © 2026 kgdtpv-netizen.
