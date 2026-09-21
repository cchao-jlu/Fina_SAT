# EchoSAT Orbit Certification

This expands manifest orbit JSON files into an auditable orbit table for EchoSAT training boundaries. It is not a runtime benchmark and does not train a model.

## Inputs

- manifest: `runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv`
- output CSV: `runs/analysis/echosat_v2_orbit_certification.csv`
- variable output CSV: `runs/analysis/echosat_v2_orbit_variables.csv`

## Sanity

- orbit rows: `39150`
- variable rows: `80014`
- base instances: `93`
- random-control rows with nonzero confidence: `0`
- full variable coverage: `True`
- duplicate variable rows: `0`
- uncovered/uncertified variable rows: `35607`
- random-control valid-variable count: `0`

## Family Summary

| family | control_type | symmetry_strength | instances | bases | orbit_rows | valid_orbit_rows | valid_orbit_vars | mean_orbit_confidence | needs_refinement_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_coloring | strong_symmetry | strong | 159 | 11 | 159 | 159 | 5348 | 1.0 | 0 |
| dominating_set_hex | weak_symmetry | weak | 34 | 2 | 374 | 187 | 374 | 0.3 | 187 |
| even_colouring | weak_symmetry | weak | 85 | 5 | 1649 | 1496 | 4522 | 0.5443298969072166 | 153 |
| php | strong_symmetry | strong | 125 | 9 | 125 | 125 | 9140 | 1.0 | 0 |
| php_exit_all | weak_symmetry | weak | 88 | 6 | 176 | 176 | 5685 | 0.6 | 0 |
| php_exit_single | weak_symmetry | weak | 122 | 8 | 366 | 244 | 9104 | 0.4 | 122 |
| random_3sat_control | non_symmetric_control | none | 429 | 31 | 35043 | 0 | 0 | 0.0 | 0 |
| subset_cardinality | weak_symmetry | weak | 102 | 6 | 918 | 816 | 5304 | 0.5333333333333333 | 102 |
| tseitin_complete | strong_symmetry | strong | 170 | 10 | 255 | 255 | 3740 | 1.0 | 0 |
| vertex_cover_torus | strong_symmetry | strong | 85 | 5 | 85 | 85 | 1190 | 1.0 | 0 |

## Usage

High-confidence rows with `valid_for_training=True` are eligible for symmetry-positive reward. Random controls keep `orbit_confidence=0` and must not enter the symmetry-positive denominator.
