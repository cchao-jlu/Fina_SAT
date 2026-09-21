# EchoSAT Canonical Order Harder-Equivalent Manifest

This manifest rewrites formula-equivalent complete_coloring/php harder-baseline rows with a canonical DIMACS clause order. It does not change variable ids, expected labels, or orbit files.

## Artifacts

- manifest CSV: `runs/analysis/echosat_canonical_order_harder_equiv_manifest.csv`
- CNF root: `data/echosat_canonical_order_harder_equiv`

## Scope

| family | base_instance_id | rows | variants | num_vars | num_clauses |
| --- | --- | --- | --- | --- | --- |
| complete_coloring | k10_color9 | 3 | base,perm_seed1730,perm_seed1731 | 90 | 775 |
| complete_coloring | k9_color8 | 3 | base,perm_seed1730,perm_seed1731 | 72 | 549 |
| php | php_p10_h9 | 3 | base,perm_seed1730,perm_seed1731 | 90 | 775 |
| php | php_p9_h8 | 3 | base,perm_seed1730,perm_seed1731 | 72 | 549 |

## Canonicalization

- Each clause is sorted by absolute variable id, then positive literal before negative literal.
- Clause rows are sorted by clause length, then lexicographically.
- This deliberately tests CDCL/adapter sensitivity to DIMACS ordering while preserving the unordered formula.
