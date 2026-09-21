# EchoSAT AdapterDelta v2 Low-Warmup Sweep

This report summarizes a fixed-checkpoint runtime sweep over lower event warmup conflict budgets. It is not training, not a learned selector, and not a solver speedup claim.

## Scope

- checkpoint: AdapterDelta v2 `iter=235.pt` unless overridden in the source protocol runs
- intended families: `complete_coloring`, `php`, `random_3sat_control`
- intended warmup conflict budgets: `1, 3, 5, 10, 20`
- intended final CPU limit: `10s`
- methods: plain, neutral weighted, static weighted, cached trace no-adapter, event adapter

## Artifacts

- observations CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_observations.csv`
- overall CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_overall.csv`
- by-family CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_by_family.csv`
- by-base CSV: `runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_by_base.csv`

## Overall

| warmup_conflicts | observations | base_instances | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 108 | 12 | 0.00661103 | 0.0357992 | -0.427392 | -0.28918 | 5798.44 | 4470.5 | 0.425926 | 0.425926 |
| 3 | 108 | 12 | 0.00758381 | 0.0611377 | -0.392833 | -0.237837 | 14784 | 13504.9 | 0.462963 | 0.351852 |
| 5 | 108 | 12 | 0.00690419 | 0.0460204 | -0.419486 | -0.263085 | 12587.5 | 11381 | 0.462963 | 0.37963 |
| 10 | 108 | 12 | 0.00653787 | 0.0850195 | -0.376459 | -0.223724 | 12281.8 | 11169.8 | 0.5 | 0.444444 |
| 20 | 108 | 12 | 0.00628263 | 0.096246 | -0.366806 | -0.218856 | 14646.1 | 13249.8 | 0.425926 | 0.453704 |

## By Family

| warmup_conflicts | family | observations | base_instances | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean | adapter_cached_final_cpu_improved_fraction | adapter_plain_protocol_improved_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | 27 | 3 | 0.00801263 | -0.178184 | -0.242343 | -0.136405 | -17936.7 | -16259.3 | 0.962963 | 0.259259 |
| 1 | php | 18 | 2 | 0.00832372 | -0.126658 | -0.146187 | -0.0249445 | 1456.67 | 1288.5 | 0.666667 | 0.666667 |
| 1 | random_3sat_control | 63 | 7 | 0.005521 | 0.173923 | -0.587043 | -0.430151 | 17211.1 | 14263.9 | 0.126984 | 0.428571 |
| 3 | complete_coloring | 27 | 3 | 0.00723607 | -0.050511 | -0.111614 | 0.0347414 | 10993 | 11264.9 | 0.888889 | 0.222222 |
| 3 | php | 18 | 2 | 0.00979794 | 0.162533 | 0.152365 | 0.283493 | 37521.3 | 36843.8 | 0.5 | 0.111111 |
| 3 | random_3sat_control | 63 | 7 | 0.00710022 | 0.080017 | -0.669127 | -0.503608 | 9912.38 | 7796.71 | 0.269841 | 0.47619 |
| 5 | complete_coloring | 27 | 3 | 0.00778356 | -0.0661559 | -0.132719 | 0.0156995 | 7500.44 | 7722.67 | 0.814815 | 0.222222 |
| 5 | php | 18 | 2 | 0.00868211 | 0.142758 | 0.114727 | 0.236599 | 32855.7 | 32349.8 | 0.833333 | 0.277778 |
| 5 | random_3sat_control | 63 | 7 | 0.00601935 | 0.0664568 | -0.695018 | -0.525331 | 8976.76 | 6957.81 | 0.206349 | 0.47619 |
| 10 | complete_coloring | 27 | 3 | 0.00777133 | -0.0500174 | -0.109412 | 0.0237699 | 7252.33 | 7953.56 | 0.888889 | 0.333333 |
| 10 | php | 18 | 2 | 0.00782489 | -0.0324537 | -0.048212 | 0.0791346 | 13023.3 | 14048.3 | 0.833333 | 0.444444 |
| 10 | random_3sat_control | 63 | 7 | 0.00564152 | 0.176456 | -0.584692 | -0.416323 | 14225.4 | 11725.7 | 0.238095 | 0.492063 |
| 20 | complete_coloring | 27 | 3 | 0.00717978 | -0.132304 | -0.18585 | -0.0457717 | 2533.78 | 3099 | 0.962963 | 0.444444 |
| 20 | php | 18 | 2 | 0.00767317 | 0.159021 | 0.152254 | 0.270428 | 38613 | 37214.8 | 0.5 | 0.333333 |
| 20 | random_3sat_control | 63 | 7 | 0.00550084 | 0.17626 | -0.592661 | -0.432831 | 12989.4 | 10753 | 0.174603 | 0.492063 |

## Best Base Rows By Budget

| warmup_conflicts | family | base_instance_id | observations | warmup_cpu_mean | adapter_cached_final_cpu_delta_mean | adapter_plain_final_cpu_delta_mean | adapter_plain_protocol_delta_mean | adapter_cached_decisions_delta_mean | adapter_cached_conflicts_delta_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | complete_coloring | k10_color9 | 9 | 0.00951267 | -0.477147 | -0.725417 | -0.619592 | -52845.3 | -48089.7 |
| 1 | php | php_p10_h9 | 9 | 0.00962311 | -0.215087 | -0.237284 | -0.114687 | 4122 | 3556.67 |
| 1 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.007449 | -0.191843 | -3.63262 | -3.44782 | -2658.67 | -2982.67 |
| 1 | complete_coloring | k9_color8 | 9 | 0.00810778 | -0.049448 | 0.00524722 | 0.11487 | -1055.67 | -800.333 |
| 1 | php | php_p9_h8 | 9 | 0.00702433 | -0.0382297 | -0.0550888 | 0.0647977 | -1208.67 | -979.667 |
| 1 | complete_coloring | k8_color7 | 9 | 0.00641744 | -0.00795744 | -0.00685956 | 0.0955054 | 91 | 112 |
| 1 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00330711 | 0.00426356 | -0.547321 | -0.381579 | 398.333 | 332.333 |
| 1 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00472667 | 0.00450578 | -0.0148717 | 0.135825 | 747 | 542.667 |
| 1 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00605389 | 0.0234104 | -1.19362 | -1.10069 | 2399 | 2003 |
| 1 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00649467 | 0.183014 | -0.0187044 | 0.165103 | 12929 | 11554.7 |
| 1 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00402356 | 0.526824 | 0.0749746 | 0.24144 | 43663.7 | 38658.3 |
| 1 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00659211 | 0.667283 | 1.22287 | 1.37666 | 62999.7 | 49738.7 |
| 3 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00774333 | -0.794614 | -4.21611 | -4.02285 | -38323.3 | -34672.3 |
| 3 | complete_coloring | k9_color8 | 9 | 0.00812167 | -0.112236 | -0.054403 | 0.0882587 | -2241.33 | -1884.67 |
| 3 | php | php_p9_h8 | 9 | 0.00873011 | -0.0677912 | -0.0855764 | 0.0444504 | -970 | -744 |
| 3 | complete_coloring | k10_color9 | 9 | 0.00958167 | -0.0244989 | -0.270491 | -0.119447 | 35534.7 | 35945.7 |
| 3 | complete_coloring | k8_color7 | 9 | 0.00400489 | -0.0147982 | -0.00994789 | 0.135413 | -314.333 | -266.333 |
| 3 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00723289 | 0.00123389 | -0.0166778 | 0.14237 | 767.667 | 561.333 |
| 3 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00687644 | 0.00363956 | -0.550217 | -0.376301 | 334.667 | 283.667 |
| 3 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00782889 | 0.0239633 | -1.17926 | -1.07515 | 2349 | 1918 |
| 3 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.004719 | 0.143616 | -0.309392 | -0.137628 | 14432.3 | 12475.7 |
| 3 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00811311 | 0.209919 | 0.0157676 | 0.209344 | 15076.7 | 13461.3 |
| 3 | php | php_p10_h9 | 9 | 0.0108658 | 0.392858 | 0.390306 | 0.522536 | 76012.7 | 74431.7 |
| 3 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00718789 | 0.972361 | 1.57201 | 1.73496 | 74749.7 | 60549.3 |
| 5 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00627467 | -0.741857 | -4.16288 | -3.96338 | -35115.3 | -31875.7 |
| 5 | complete_coloring | k9_color8 | 9 | 0.00824967 | -0.115636 | -0.0594448 | 0.0824445 | -3883 | -3459.33 |
| 5 | php | php_p9_h8 | 9 | 0.00690367 | -0.0806881 | -0.100886 | 0.0191659 | -2914 | -2688.67 |
| 5 | complete_coloring | k10_color9 | 9 | 0.0102072 | -0.0680011 | -0.329219 | -0.174824 | 26951.7 | 27149 |
| 5 | complete_coloring | k8_color7 | 9 | 0.00489378 | -0.0148302 | -0.00949278 | 0.139478 | -567.333 | -521.667 |
| 5 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00583889 | 0.00355733 | -0.0158094 | 0.140753 | 699 | 491.333 |
| 5 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00615633 | 0.00723456 | -0.550015 | -0.374365 | 380.667 | 336 |
| 5 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.006362 | 0.0146001 | -1.20426 | -1.09236 | 1330.33 | 1103.67 |
| 5 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.00431389 | 0.110986 | -0.339408 | -0.165629 | 11396.7 | 9876.67 |
| 5 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00615322 | 0.233249 | 0.0359499 | 0.235362 | 16071.3 | 14377 |
| 5 | php | php_p10_h9 | 9 | 0.0104606 | 0.366203 | 0.330341 | 0.454031 | 68625.3 | 67388.3 |
| 5 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00703644 | 0.837428 | 1.37129 | 1.54231 | 68074.7 | 54395.7 |
| 10 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00571067 | -0.782787 | -4.19632 | -3.98645 | -37474 | -33975.3 |
| 10 | complete_coloring | k9_color8 | 9 | 0.00766767 | -0.135549 | -0.0754203 | 0.0560635 | -4306 | -4034.33 |
| 10 | php | php_p9_h8 | 9 | 0.00713511 | -0.105385 | -0.122028 | 0.00457283 | -3514.33 | -3248.67 |
| 10 | complete_coloring | k8_color7 | 9 | 0.00538067 | -0.0138484 | -0.0111617 | 0.120334 | -361.333 | -335.667 |
| 10 | complete_coloring | k10_color9 | 9 | 0.0102657 | -0.000654444 | -0.241653 | -0.105088 | 26424.3 | 28230.7 |
| 10 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00571022 | 0.001954 | -0.557211 | -0.391214 | 380.667 | 336 |
| 10 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00663333 | 0.00647322 | -0.00866489 | 0.144667 | 863 | 603.667 |
| 10 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00614022 | 0.0117532 | -1.2038 | -1.10208 | 1293.67 | 1064.33 |
| 10 | php | php_p10_h9 | 9 | 0.00851467 | 0.0404778 | 0.0256044 | 0.153696 | 29561 | 31345.3 |
| 10 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.003204 | 0.0965078 | -0.352686 | -0.189214 | 10398.3 | 8984 |
| 10 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00500889 | 0.223846 | 0.0285917 | 0.237729 | 16239.3 | 14582.3 |
| 10 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00708333 | 1.67745 | 2.19724 | 2.3723 | 107877 | 90484.7 |
| 20 | random_3sat_control | random_3sat_control_v260_c1097_seed3305 | 9 | 0.00571433 | -0.745191 | -4.22914 | -4.0522 | -35378.3 | -32043.3 |
| 20 | complete_coloring | k10_color9 | 9 | 0.00983889 | -0.241731 | -0.460604 | -0.314767 | 10301.3 | 11922.7 |
| 20 | complete_coloring | k9_color8 | 9 | 0.00822756 | -0.14119 | -0.088193 | 0.0471545 | -2390.67 | -2340 |
| 20 | php | php_p9_h8 | 9 | 0.00542322 | -0.115742 | -0.134242 | -0.0183404 | -3158.67 | -3006.33 |
| 20 | complete_coloring | k8_color7 | 9 | 0.00347289 | -0.0139912 | -0.00875133 | 0.130297 | -309.333 | -285.667 |
| 20 | random_3sat_control | random_3sat_control_v220_c928_seed3303 | 9 | 0.00456156 | 0.00572633 | -0.547587 | -0.371049 | 380.667 | 336 |
| 20 | random_3sat_control | random_3sat_control_v160_c704_seed2615 | 9 | 0.00371733 | 0.00928344 | -0.00773856 | 0.147447 | 1032.67 | 763.667 |
| 20 | random_3sat_control | random_3sat_control_v300_c1266_seed3307 | 9 | 0.00608622 | 0.0122793 | -1.20231 | -1.09988 | 1323.33 | 1103.33 |
| 20 | random_3sat_control | random_3sat_control_v180_c760_seed3301 | 9 | 0.004349 | 0.0390729 | -0.410551 | -0.234269 | 4257 | 3661.67 |
| 20 | random_3sat_control | random_3sat_control_v220_c942_seed3304 | 9 | 0.00690567 | 0.227361 | 0.0241262 | 0.202172 | 15722.3 | 14141.3 |
| 20 | php | php_p10_h9 | 9 | 0.00992311 | 0.433783 | 0.43875 | 0.559196 | 80384.7 | 77436 |
| 20 | random_3sat_control | random_3sat_control_v260_c1113_seed3306 | 9 | 0.00717178 | 1.68529 | 2.22456 | 2.37797 | 103588 | 87308 |

## Reading Rules

- `adapter_cached_final_cpu_delta_mean < 0` means the adapter changed final search beneficially after paying the same warmup/event path.
- `adapter_plain_protocol_delta_mean < 0` is the stricter end-to-end comparison against basic Glucose.
- If low budgets preserve complete_coloring/php `adapter_cached_final_cpu_delta_mean` while reducing `warmup_cpu_mean`, the next step is a deployable pre-final gate.
- If low budgets erase the adapter-cached signal, the next step is objective work with low-warmup traces rather than selector training.
