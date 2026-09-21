# EchoSAT Canonical DIMACS Order Audit

This audit reruns the low-warmup protocol on canonicalized DIMACS order for formula-equivalent complete_coloring/php harder-baseline rows. It is an order-sensitivity diagnostic, not training and not a speedup claim.

## Artifacts

- canonical observations CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_low_warmup_sweep_observations.csv`
- pair deltas CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_pair_deltas.csv`
- summary CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_canonical_order_summary.csv`

## Key Findings

- Paired order-delta rows: 180.
- Max absolute family-level plain final CPU order delta: 0.215882s.
- Max absolute family-level adapter final CPU order delta: 0.305022s.
- Max absolute family-level adapter-vs-cached delta shift: 0.298688s.
- Canonicalization does not justify a speedup claim. It confirms that DIMACS ordering materially changes both plain and adapter-guided CDCL paths on these formula-equivalent rows.

## Overall By Family

| warmup_conflicts | family | rows | base_instances | plain_cpu_order_delta_mean | adapter_final_cpu_order_delta_mean | adapter_protocol_order_delta_mean | adapter_cached_delta_order_delta_mean | adapter_plain_protocol_delta_order_delta_mean | event_l2_order_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | 18 | 2 | 0.101569 | 0.305022 | 0.342731 | 0.298688 | 0.241163 | 0.0881742 |
| 1 | php | 18 | 2 | 0.188177 | 0.191998 | 0.168035 | 0.163049 | -0.0201425 | 0.073733 |
| 3 | complete_coloring | 18 | 2 | 0.0704094 | 0.144438 | 0.136629 | 0.160235 | 0.0662191 | 0.494764 |
| 3 | php | 18 | 2 | 0.196921 | -0.020807 | -0.0640041 | -0.0473241 | -0.260925 | 0.605932 |
| 5 | complete_coloring | 18 | 2 | 0.0584231 | 0.0998362 | 0.105379 | 0.119073 | 0.0469564 | 0.0131556 |
| 5 | php | 18 | 2 | 0.199472 | -0.0760504 | -0.0988891 | -0.116232 | -0.298361 | 0.364031 |
| 10 | complete_coloring | 18 | 2 | 0.0743496 | 0.109879 | 0.120945 | 0.124477 | 0.0465958 | 0.520137 |
| 10 | php | 18 | 2 | 0.215882 | 0.128033 | 0.0908038 | 0.093608 | -0.125079 | -1.92942 |
| 20 | complete_coloring | 18 | 2 | 0.0909278 | 0.0571848 | 0.0574809 | 0.0664334 | -0.033447 | 0.986399 |
| 20 | php | 18 | 2 | 0.188642 | -0.257622 | -0.290822 | -0.273192 | -0.479464 | 0.574605 |

## By Base

| warmup_conflicts | family | base_instance_id | rows | plain_unguided_glucose_final_cpu_time_order_delta_mean | event_adapter_final_final_cpu_time_order_delta_mean | event_adapter_final_protocol_accounted_time_order_delta_mean | adapter_cached_final_cpu_delta_order_delta_mean | adapter_plain_protocol_delta_order_delta_mean | event_state_l2_sum_order_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k10_color9 | 9 | 0.138122 | 0.664937 | 0.706521 | 0.690499 | 0.568398 | 0.0603485 |
| 1 | complete_coloring | k9_color8 | 9 | 0.0650152 | -0.0548933 | -0.0210579 | -0.0931229 | -0.0860732 | 0.116 |
| 1 | php | php_p10_h9 | 9 | 0.363012 | 0.429236 | 0.429307 | 0.422812 | 0.0662951 | -0.0219065 |
| 1 | php | php_p9_h8 | 9 | 0.0133421 | -0.0452396 | -0.0932379 | -0.096715 | -0.10658 | 0.169373 |
| 3 | complete_coloring | k10_color9 | 9 | 0.0771711 | 0.295237 | 0.284521 | 0.361108 | 0.20735 | 0.598165 |
| 3 | complete_coloring | k9_color8 | 9 | 0.0636478 | -0.00636133 | -0.011264 | -0.0406378 | -0.0749118 | 0.391363 |
| 3 | php | php_p10_h9 | 9 | 0.390298 | -0.0110311 | -0.0277914 | -0.0205489 | -0.418089 | 0.901276 |
| 3 | php | php_p9_h8 | 9 | 0.00354422 | -0.0305829 | -0.100217 | -0.0740993 | -0.103761 | 0.310588 |
| 5 | complete_coloring | k10_color9 | 9 | 0.05733 | 0.225137 | 0.225999 | 0.298956 | 0.168669 | 0.505152 |
| 5 | complete_coloring | k9_color8 | 9 | 0.0595161 | -0.0254642 | -0.0152397 | -0.0608102 | -0.0747558 | -0.478841 |
| 5 | php | php_p10_h9 | 9 | 0.389558 | -0.105303 | -0.10108 | -0.133422 | -0.490638 | 1.35932 |
| 5 | php | php_p9_h8 | 9 | 0.00938644 | -0.0467976 | -0.0966978 | -0.0990409 | -0.106084 | -0.631261 |
| 10 | complete_coloring | k10_color9 | 9 | 0.0859778 | 0.243281 | 0.252705 | 0.304689 | 0.166727 | 1.12661 |
| 10 | complete_coloring | k9_color8 | 9 | 0.0627213 | -0.0235224 | -0.0108145 | -0.0557349 | -0.0735358 | -0.0863342 |
| 10 | php | php_p10_h9 | 9 | 0.422657 | 0.290016 | 0.281225 | 0.269339 | -0.141431 | -2.30824 |
| 10 | php | php_p9_h8 | 9 | 0.00910811 | -0.03395 | -0.0996175 | -0.0821229 | -0.108726 | -1.5506 |
| 20 | complete_coloring | k10_color9 | 9 | 0.114119 | 0.118362 | 0.115589 | 0.177939 | 0.00147016 | 4.78652 |
| 20 | complete_coloring | k9_color8 | 9 | 0.0677368 | -0.00399267 | -0.00062729 | -0.045072 | -0.0683641 | -2.81372 |
| 20 | php | php_p10_h9 | 9 | 0.371216 | -0.504583 | -0.510571 | -0.48668 | -0.881786 | 3.70516 |
| 20 | php | php_p9_h8 | 9 | 0.00606767 | -0.0106603 | -0.0710739 | -0.0597038 | -0.0771416 | -2.55595 |

## Interpretation

- `*_order_delta_mean` is canonical-order value minus original-order value.
- Large plain or adapter deltas imply CDCL/order sensitivity, so original complete_coloring/php differences cannot be treated as family-specific symmetry evidence.
- If canonicalization collapses complete_coloring/php behavior, the next step is to canonicalize future runtime protocols.
- If canonicalization still leaves adapter-specific instability, the next step is objective/permutation robustness work, not selector training.
