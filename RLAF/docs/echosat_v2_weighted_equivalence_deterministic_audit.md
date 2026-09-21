# EchoSAT v2 Weighted Neutral Equivalence Audit

- Status: **ACCEPT**
- Gate mode: `deterministic`
- Input: `runs/analysis/echosat_v2_weighted_equivalence_deterministic.csv`
- Expected manifest: `runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv`
- Pairs: 4197
- Accepted pairs: 4197
- Rejected pairs: 0
- Missing expected pairs: 0
- Mean neutral-minus-plain final CPU time: -0.000938044556
- Maximum absolute final CPU delta: 0.1258
- CPU time is diagnostic-only and does not affect acceptance.

Acceptance requires valid rows and exact equality of final result, input final_solved status, decisions, and conflicts.
