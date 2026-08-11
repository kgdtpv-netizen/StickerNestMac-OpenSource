# Architecture

```text
SwiftUI UI
   │
   ├── native import, rendering, safety checks, and export
   │
   └── external Python process
          │
          ├── OpenCV alpha-contour preprocessing
          ├── grid-based candidate placement
          ├── orientation and gap policies
          └── JSON layout + preview output
```

## Native application

`Sources/StickerNestMac.swift` owns the current SwiftUI interface, file import, preview rendering, placement validation, process lifecycle, and output handling. External solver memory is sampled while the process runs; termination escalates from SIGTERM to SIGKILL when needed.

## Solver

`Tools/auto_nest.py` converts alpha masks to a down-sampled work grid, explores placement candidates, and emits a JSON layout. The effective gap is quantized by the work grid and is surfaced separately from the nominal requested gap.

## Local learning and policy data

The public solver runs with generic built-in defaults. Production-derived
`manual_layout_policy.json` and `manual_stagger_policy.json` files are neither
tracked nor bundled. The solver treats absent optional policy files as empty
configuration.

The native app can learn an optional profile from a folder explicitly selected
by the user. Generated profiles remain under the user's Application Support
directory. `build.zsh` copies only `auto_nest.py` and
`analyze_manual_layouts.py`; it does not copy `Resources/` wholesale.

## Trust boundaries

Imported images and solver output are untrusted inputs. Callers should validate file types, placement bounds, overlap, process resource use, and final physical cut clearance. The application does not upload artwork or call remote services.
