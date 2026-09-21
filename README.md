# Fina_SAT / EchoSAT research snapshot

This repository contains the EchoSAT SAT-symmetry research code and selected experimental evidence built on RLAF. The working Python project remains in `RLAF/`; run its commands from that directory.

Start with **[NEXT_PLAN.md](NEXT_PLAN.md)** for the current research decision and staged acceptance criteria, and **[EXPERIMENT_SNAPSHOT.md](EXPERIMENT_SNAPSHOT.md)** for the published evidence and reproducibility limits.

## Status

- Research snapshot dated 2026-09-21; experiment artifacts include work through 2026-07-21.
- No established general or end-to-end solver speedup claim.
- v2 Stage 5 reached 20 iterations, but all four recorded checkpoint-selection gates failed.
- Historical documentation is preserved and may describe superseded objectives or unavailable experiments.
- Existing licenses and third-party solver notices remain in place; this snapshot does not relicense upstream work.

## Layout

- `RLAF/src`, `RLAF/train_*.py`, `RLAF/configs`, `RLAF/tests`: implementation and tests.
- `RLAF/solvers`: Glucose and modified Glucose source, without compiled binaries.
- `RLAF/docs`: historical reports and designs, including negative results.
- `RLAF/data`: selected generated CNF datasets and orbit metadata.
- `published`: explicitly selected raw tables, configurations, reports, and experiment logs.
- `tools/audit_snapshot.py`: standard-library-only snapshot audit and inventory.

## Reproducibility limits

Model checkpoints, trace tensors, virtual environments, private service state, and most historical runs are not included. Checkpoint hashes are recorded rather than implying model-based experiments can run immediately after cloning. Historical files contain legacy absolute paths; resolve or regenerate manifests before running them. Canonical CNFs are included, but legacy absolute train/val symlinks are excluded. Recreate split directories from the manifest before training.

`RLAF/setup.py` reflects the historical CUDA/Linux environment and is not a portable macOS lockfile. `RLAF/build_solvers.sh` also references March sources not present in this snapshot. For the available Glucose sources, inspect each `simp/Makefile` and build the appropriate platform target explicitly. Consult `RLAF/README.md` for historical environment guidance, not a promise of a fresh-clone turnkey setup.

To inspect the shipped evidence without installing training dependencies:

```sh
python3 tools/audit_snapshot.py
```
