# Data and Asset Notice

This repository intentionally excludes private production datasets and third-party artwork from the original internal development environment.

The public tree contains code, documentation, and tests only. It does not include:

- customer or celebrity artwork;
- TIFF/PSD/PLT production files;
- production QR images or mappings;
- local file manifests and absolute paths;
- internal handoff, session, or optimization logs;
- private benchmark screenshots.
- production-derived layout policy files such as `manual_layout_policy.json` or `manual_stagger_policy.json`.

The build copies an explicit allowlist of runtime scripts and never copies the
repository's `Resources/` directory wholesale. Optional profiles created from a
user's own inputs remain local to that user's Application Support directory.

Do not add an asset unless you own it or its license explicitly permits redistribution in this repository. The MIT License covers the repository's code; it does not grant rights to third-party trademarks, likenesses, or artwork.
