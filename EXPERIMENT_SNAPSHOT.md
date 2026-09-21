# Experiment Snapshot

Date: 2026-09-21

This is a selected, size-bounded publication snapshot. It is not the complete local workspace.

## Included

- `NEXT_PLAN.md`, current implementation, tests, configs, docs, and solver source under `RLAF/`.
- Generated symmetry CNFs and metadata under `RLAF/data/echosat_symmetry_grpo_v1_canonical/`.
- Orbit certification summaries/tables and weighted-equivalence audit summaries/CSVs in `published/analysis/`.
- v1.2/v1.7 targeted acceptance and failure-attribution tables.
- EchoSAT v2 Stage 4 and Stage 5 raw reward-replay CSVs, Stage 5 config and bootstrap log; model checkpoints are intentionally excluded.
- Root `README.md` and `.gitignore`.

## Key published evidence

- Orbit certification: 93 base instances, 80,014 variable rows, 39,150 orbit rows; random controls have zero valid orbit confidence rows.
- Stage 4 v2 replay: 1,184 rows, 82 eligible, 37 positive rows; blocked rows remain non-positive.
- Stage 5 Retry1: 20 iterations completed; 21,072 replay rows, 2,048 eligible, 872 positive advantages; no blocked-positive rows in the published replay. Validation gates at iterations 0, 5, 10 and 15 failed, so no `best.pt` was promoted.
- Weighted neutral equivalence: deterministic and CPU audit summaries report 4,197/4,197 accepted pairs, with different acceptance criteria; this is not a claim of identical search traces in the CPU audit.
- Historical runtime reports show protocol overhead and earlier weighted-path coverage issues; they must be read as diagnostic evidence, not an end-to-end speedup claim.

## Excluded

- Virtual environments, caches, W&B state, generated outputs, compiled binaries, object files, checkpoints, trace tensors, the 9.7 GB source bundle, and most raw runtime tables.
- The local `data/` directory outside `RLAF/`, the full stress dataset (some individual CNFs are about 98 MB), and legacy absolute split symlinks. The compact stress-smoke dataset is included.
- Any credentials, tokens, key material, or private service state.

## Reproducibility caveats

- Historical manifests contain absolute paths from other machines. Use the included datasets and regenerate paths before execution.
- The snapshot has no portable dependency lockfile. `RLAF/setup.py` describes the historical environment.
- Source code and selected evidence are available; complete model-based reproduction requires the excluded checkpoints or retraining.
- Checkpoint fingerprints are in `published/checkpoint_inventory.csv`. They identify locally available models without publishing their binary weights.
- `published/snapshot_audit.json` records counts recomputed from the included raw replay and manifests. Run `python3 tools/audit_snapshot.py` to recompute and compare them.
- The raw deterministic/CPU equivalence execution tables (about 94 MB combined) are excluded; per-pair audit CSVs and reports are included. Rerunning solver-level equivalence requires rebuilding the binaries and remapping the manifest.
- Historical absolute paths and author attribution are preserved as provenance. No claim is made that the old configurations are directly executable on a fresh clone.
