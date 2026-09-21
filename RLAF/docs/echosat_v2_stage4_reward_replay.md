# EchoSAT v2 Offline Replay Audit

- input: `runs/analysis/echosat_v2_stage4_reward_replay/iter=000000_solver_stats.csv`
- rows: `1184`
- eligible: `82`
- blocked: `1102`
- invalid eligibility: `0`

## Checks

- `blocked_rows_non_positive`: `True` — blocked=1102 positive=0 invalid_eligibility=0
- `eligible_positive_exists`: `True` — eligible=82 positive=37
- `all_v2_stage4_checks`: `True` — blocked_rows_non_positive=True eligible_positive_exists=True

## Variant Summary

- eligible rows: `82`
- positive-capable variants: `7`
- hard-blocked variants: `38`
- missing diagnostics: `none`
- invalid diagnostic values: `0`

| base | variant | eligible rows | positive capable | hard blocked |
| --- | --- | ---: | --- | --- |
| `k10_color9` | `base` | 0 | False | False |
| `k10_color9` | `perm_seed1730` | 0 | False | False |
| `k10_color9` | `perm_seed1731` | 0 | False | False |
| `k9_color8` | `base` | 12 | True | False |
| `k9_color8` | `perm_seed1730` | 0 | False | True |
| `k9_color8` | `perm_seed1731` | 16 | True | False |
| `php_p10_h9` | `base` | 0 | False | True |
| `php_p10_h9` | `perm_seed1730` | 0 | False | False |
| `php_p10_h9` | `perm_seed1731` | 0 | False | False |
| `php_p10_h9` | `perm_seed1732` | 0 | False | False |
| `php_p10_h9` | `perm_seed1733` | 0 | False | False |
| `php_p10_h9` | `perm_seed1734` | 0 | False | True |
| `php_p10_h9` | `perm_seed1735` | 0 | False | False |
| `php_p10_h9` | `perm_seed1736` | 0 | False | False |
| `php_p10_h9` | `perm_seed1737` | 0 | False | False |
| `php_p10_h9` | `perm_seed1738` | 0 | False | False |
| `php_p10_h9` | `perm_seed1739` | 0 | False | False |
| `php_p10_h9` | `perm_seed1740` | 0 | False | True |
| `php_p10_h9` | `perm_seed1741` | 0 | False | True |
| `php_p10_h9` | `perm_seed1742` | 0 | False | False |
| `php_p10_h9` | `perm_seed1743` | 7 | True | False |
| `php_p10_h9` | `perm_seed1744` | 0 | False | False |
| `php_p10_h9` | `perm_seed1745` | 0 | False | False |
| `php_p9_h8` | `base` | 13 | True | False |
| `php_p9_h8` | `perm_seed1730` | 0 | False | True |
| `php_p9_h8` | `perm_seed1731` | 0 | False | True |
| `php_p9_h8` | `perm_seed1732` | 10 | True | False |
| `php_p9_h8` | `perm_seed1733` | 0 | False | True |
| `php_p9_h8` | `perm_seed1734` | 0 | False | True |
| `php_p9_h8` | `perm_seed1735` | 0 | False | True |
| `php_p9_h8` | `perm_seed1736` | 0 | False | True |
| `php_p9_h8` | `perm_seed1737` | 0 | False | True |
| `php_p9_h8` | `perm_seed1738` | 0 | False | True |
| `php_p9_h8` | `perm_seed1739` | 0 | False | False |
| `php_p9_h8` | `perm_seed1740` | 10 | True | False |
| `php_p9_h8` | `perm_seed1741` | 14 | True | False |
| `php_p9_h8` | `perm_seed1742` | 0 | False | True |
| `php_p9_h8` | `perm_seed1743` | 0 | False | True |
| `php_p9_h8` | `perm_seed1744` | 0 | False | True |
| `php_p9_h8` | `perm_seed1745` | 0 | False | False |
| `random_3sat_control_v45_c191_seed1924` | `base` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1730` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1731` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1732` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1733` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1734` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1735` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1736` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1737` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1738` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1739` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1740` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1741` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1742` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1743` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1744` | 0 | False | True |
| `random_3sat_control_v45_c191_seed1924` | `perm_seed1745` | 0 | False | True |
| `subset_cardinality_bw18` | `base` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1730` | 0 | False | True |
| `subset_cardinality_bw18` | `perm_seed1731` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1732` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1733` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1734` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1735` | 0 | False | True |
| `subset_cardinality_bw18` | `perm_seed1736` | 0 | False | True |
| `subset_cardinality_bw18` | `perm_seed1737` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1738` | 0 | False | True |
| `subset_cardinality_bw18` | `perm_seed1739` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1740` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1741` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1742` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1743` | 0 | False | False |
| `subset_cardinality_bw18` | `perm_seed1744` | 0 | False | True |
| `subset_cardinality_bw18` | `perm_seed1745` | 0 | False | False |

## Base Summary

| base | eligible rows | eligible variants | worst variant score |
| --- | ---: | ---: | ---: |
| `k10_color9` | 0 | 0 | -0.517548258576 |
| `k9_color8` | 28 | 2 | 0.0498055545995 |
| `php_p10_h9` | 7 | 1 | -0.765780398788 |
| `php_p9_h8` | 47 | 4 | -0.158122177805 |
| `random_3sat_control_v45_c191_seed1924` | 0 | 0 | -7.4326370614 |
| `subset_cardinality_bw18` | 0 | 0 | -0.379899717154 |

## Hard-Safety Rejections

| reason | rows |
| --- | ---: |
| `control` | 272 |
| `hard_safety_total` | 548 |
| `invalid_static_baseline` | 0 |
| `invalid_symmetry_orbit_evidence` | 272 |
| `missing_plain_baseline` | 0 |
| `missing_static_baseline` | 0 |
| `near_cap` | 0 |
| `plain_result_mismatch` | 0 |
| `plain_solved_guided_unsolved` | 6 |
| `plain_unsolved` | 0 |
| `static_result_mismatch` | 0 |
| `static_solved_guided_unsolved` | 6 |
| `static_unsolved` | 0 |
| `weighted_risk` | 336 |
