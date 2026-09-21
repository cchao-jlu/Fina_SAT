完整方案如下，建议命名为 targeted v2 mechanism audit。

  目标

  验证少数 positive runtime case 是否真的形成机制链：

  event identity signal -> adapter orbit separation -> final search changes -> decisions/conflicts/CPU 改善

  这一步仍然不做：

  - 不训练
  - 不做 gate/selector
  - 不扩 full runtime benchmark
  - 不写 solver speedup claim

  输入

  固定使用现有 v2 runtime 结果：

  - runs/analysis/symmetry_runtime_benchmark_v2_attribution.csv
  - runs/analysis/symmetry_runtime_positive_v2_base_summary.csv
  - runs/analysis/symmetry_runtime_positive_v2_observations.csv
  - 现有 W05 orbit audit 只作参考，不作为 full evidence

  阶段 1：candidate qualification

  先把现有 strict_positive 再分层：

  - strong_strict_positive
      - final CPU down majority
      - mean 或 median final CPU delta 为负
      - decisions 或 conflicts down majority
      - no majority search worsening

  - weak_strict_positive
      - 满足 majority 方向，但 mean/median CPU 或 search delta 很弱、不一致、或 variant-mixed

  - control_perturbation
      - non-symmetric control 中 adapter 改变搜索，但不算 symmetry-specific evidence

  优先级：

  1. dominating_set_hex_3x6_s4：主 symmetry candidate
  2. subset_cardinality_bw12：variant-mixed symmetry/weak-symmetry candidate
  3. random_3sat_control_v20_c85_seed1901：control perturbation check，可选

  阶段 2：targeted per-repeat representation/orbit audit

  不要全量跑 v2，只补上述 candidates。

  输出必须保留 repeat 维度：

  - base_instance_id
  - variant
  - repeat_id
  - solver_seed
  - warmup_seed
  - final_seed
  - trace/event identifier 或 event-state hash
  - event L2 / event nonzero vars
  - graph gate evidence/open
  - orbit validity
  - event identity gain
  - adapter identity gain
  - adapter mu/rho separation
  - final CPU delta vs cached
  - final decisions delta vs cached
  - final conflicts delta vs cached
  - protocol overhead delta

  核心要求：representation evidence 和 runtime delta 必须能按 base_instance_id + variant + repeat_id 对齐。

  阶段 3：dominating_set_hex_3x6_s4 deeper orbit join

  这是第一主线。

  要回答：

  - conflicts 下降的 rows 是否有更强 event identity signal？
  - adapter orbit separation 是否在 improved rows 更强？
  - failed/weak rows 是否对应 event weak、orbit invalid、adapter weak？
  - permutation variants 下 identity/separation 是否稳定？
  - runtime improvement 是否主要来自 conflicts drop，而不是 CPU noise？

  结论只允许写：

  - mechanism aligned
  - mechanism partially aligned
  - mechanism not aligned

  不要写 speedup。

  阶段 4：subset_cardinality_bw12 variant diagnosis

  这是第二主线，重点解释 variant split。

  比较：

  - base
  - perm_seed1730
  - perm_seed1731

  重点看 perm_seed1730 为什么 decisions/conflicts 变差：

  - event L2 是否异常？
  - graph gate evidence 是否异常？
  - orbit identity 是否弱？
  - adapter separation 是否方向不一致？
  - warmup trace 是否偏离？
  - 是否只是某个 repeat 的 solver seed 噪声？
  - 是否存在 over-adaptation 或 non-robust permutation behavior？

  这一步的目标不是证明它有效，而是判断它是否暴露 adapter objective 的问题。

  阶段 5：optional random control check

  random_3sat_control_v20_c85_seed1901 单独处理。

  目的：

  - 判断 adapter 是否只是一般性扰动搜索；
  - 对比 non-symmetric control 的 event/adapter evidence 是否也能产生 decisions change；
  - 防止把 generic perturbation 误写成 symmetry benefit。

  报告中必须单列，不并入 symmetry-positive evidence。

  阶段 6：产物

  建议产物：

  - docs/symmetry_targeted_mechanism_audit_v2.md
  - runs/analysis/symmetry_targeted_mechanism_v2_candidate_summary.csv
  - runs/analysis/symmetry_targeted_mechanism_v2_repeat_join.csv
  - runs/analysis/symmetry_targeted_mechanism_v2_orbit_rows.csv
  - runs/analysis/symmetry_targeted_mechanism_v2_subset_variant_diagnosis.csv
  - 可选：runs/analysis/symmetry_targeted_mechanism_v2_random_control.csv

  报告结构：

  1. Scope and Non-Claims
  2. Candidate Qualification
  3. Per-Repeat Join Method
  4. Dominating Set Hex Mechanism
  5. Subset Cardinality Variant Diagnosis
  6. Random Control Check
  7. Decision and Next Step

  阶段 7：exit criteria

  完成 targeted audit 后按结果分叉：

  - 如果 dominating_set_hex_3x6_s4 mechanism aligned：
    下一步扩 same-family/scale targeted audit，例如 nearby hex ladder，不做 gate。

  - 如果 subset_cardinality_bw12 是 variant-mixed：
    回到 adapter objective，重点处理 permutation robustness。

  - 如果 random control 也强，而 symmetry candidates 不强：
    结论是 adapter generic perturbation，不支持 symmetry-specific gate。

  - 如果 representation evidence 和 runtime delta 无关：
    停止 runtime 方向，回到 representation/adapter loss。

  - 只有当多个 symmetry family 出现 stable aligned mechanism，并且 overhead 有下降方案时，才重新讨论 conservative rule-based gate。