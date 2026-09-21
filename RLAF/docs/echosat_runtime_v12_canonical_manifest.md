# EchoSAT Runtime Protocol v1.2 Canonical Manifest

This manifest is the canonical-order input for the v1.2 runtime protocol. Variable ids, orbit files, and expected labels are preserved; only literal order inside clauses and clause row order are normalized.

## Artifacts

- manifest CSV: `runs/analysis/echosat_runtime_v12_canonical_manifest.csv`
- CNF root: `data/echosat_runtime_v12_canonical`

## Scope

| role | family | rows | base_instances | variants | num_vars_min | num_vars_max | num_clauses_min | num_clauses_max | source_manifests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | complete_coloring | 9 | 3 | 3 | 56 | 90 | 372 | 775 | harder_baseline_target |
| main | php | 6 | 2 | 3 | 72 | 90 | 549 | 775 | harder_baseline_target |
| main | random_3sat_control | 21 | 7 | 3 | 160 | 300 | 704 | 1266 | harder_baseline_target |
| main | subset_cardinality | 9 | 3 | 3 | 33 | 49 | 76 | 108 | runtime_benchmark_v2_labeled |

## Canonicalization

- Each clause is sorted by absolute variable id, then positive literal before negative literal.
- Clause rows are sorted by clause length, then lexicographically.
- Original-order results remain order-sensitivity diagnostics and are not mixed into the v1.2 main tables.
