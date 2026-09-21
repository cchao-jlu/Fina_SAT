# PROJECT CONTEXT

## 当前目标

当前目标不是继续打磨论文，而是判断这个项目的模型和实验结果能否支撑顶会级 claim。

核心实验问题已经从早期 Glucose/Online-Consistent workflow 转向：

- 在强 baseline `March + CaDiCaL` union 下，神经引导是否还能解出强 solver 都解不出的实例。
- 这些 neural-only solves 是否能由固定、非 oracle 的 selector 找到，而不是事后挑 sample。
- 这种收益是否能在扩大后的 transition-band held-out set 上稳定出现。

当前最有希望的方向是：

- March-trained stochastic neural guidance / sampled March policy
- fixed-budget sample generation
- 1s internal March early-trace probe
- selector policy `probe_solved_then_high_deadends`
- 目标集合：`March/CaDiCaL both-unknown` transition-band instances

早期 `online_consistent_boundary400` 和 `local_reopen_guarded` 已经不应作为顶会性能主线。它们可以保留为 frozen Glucose-workflow 的历史结果或内部 ablation，但强 baseline 下不够。

## 已经做了哪些尝试

### 1. Glucose / Online-Consistent / Local Boundary Correction 线

已经完成过一条论文式收束：

- `online_consistent_boundary400` 作为 conservative selector
- `local_reopen_guarded` 作为 local boundary correction ablation
- full400 repeated runtime、seed robustness、300/350 appendix、Glucose/CaDiCaL baseline、paper-ready tables/figures、LaTeX draft

结论：

- 在 Glucose neural workflow 内部，Online-Consistent 和 Local Boundary Correction 有清楚的风险控制/边界修补证据。
- 但 March/CaDiCaL 强 solver baseline 下，这条线不足以构成顶会性能 claim。
- 不应继续在 polarity / SBE / pairwise veto / 更复杂 old selector 上堆模型。

### 2. Strong-solver gate

已经做了 `March + CaDiCaL` transition-band gate。

重要结果见：

- `docs/benchmark_transition_band_expanded_gate.md`
- `runs/analysis/benchmark_transition_band_expanded/combined.csv`
- `runs/analysis/benchmark_transition_band_expanded/summary.csv`
- `runs/analysis/benchmark_transition_band_expanded/solver_overlap.csv`
- `runs/analysis/benchmark_transition_band_expanded/both_unknown_subset.csv`

扩大后的 both-unknown 候选：

```text
sizes: 410, 425, 440
instances per size: 50
March/CaDiCaL both-unknown total: 49

410: 5 / 50
425: 14 / 50
440: 30 / 50
```

这 49 个 both-unknown 是当前最重要的模型 gate 数据源。

### 3. Focused sampled March guidance

已有 focused evidence：

- `410/3sat_2.cnf`: stable complement, 35/48 strict-60 sampled solves
- `440/3sat_8.cnf`: low-probability complement, 4/48 strict-60 sampled solves

固定预算 selector 诊断：

- static cheap selector top-2/top-4 recovered 4/5 positive seed groups
- top-8 recovered 5/5
- 1s early trace `probe_solved_then_high_deadends` recovered 4/6 focused seed groups

结论：

- 神经 sampled guidance 确实存在 strong-solver complementarity。
- 但 focused cases 太少，不能作为顶会主证据。
- oracle sampled result 不能写成 deployable method。

### 4. Learned selector diagnostic

见：

- `docs/benchmark_march_learned_sample_selector.md`
- `analyze_march_learned_sample_selector.py`

结论：

- 在 focused diagnostic 上，learned RF / logistic 没有超过简单 `probe_dead_ends_in_main` baseline。
- 现在不应声称 learned selector 是贡献。
- 只有 expanded held-out data 上 learned selector 明确超过 simple baseline，才值得升级成方法点。

### 5. Expanded early-trace gate

当前正在推进：

- runner: `run_march_expanded_early_trace_gate.py`
- doc: `docs/benchmark_march_expanded_early_trace_gate.md`
- output dir: `runs/analysis/benchmark_march_expanded_early_trace_gate/`

已完成 first-5 smoke：

```text
5 instances x 1 seed x 8 samples
policy: probe_solved_then_high_deadends
top_k: 2
probe_cpu_lim: 1.0
solved: 1 / 5
```

唯一 solved expanded held-out strong-union-unsolved instance：

```text
410/3sat_12.cnf
sample_seed=1729
sample_id=5
selector_rank=1
CPU time=14.5353s
```

这是真正重要的正结果：固定非 oracle early-trace selector 在 March/CaDiCaL both-unknown 扩展集合上找到了 neural-only solve。

已补完 `limit-instances=15`：

```bash
python run_march_expanded_early_trace_gate.py \
  --limit-instances 15 \
  --sample-seeds 1729 \
  --num-samples 8 \
  --top-k 2 \
  --probe-cpu-lim 1.0 \
  --policy probe_solved_then_high_deadends \
  --resume
```

最终结果：

```text
completed summaries: 15 / 15
solved groups: 1 / 15
solved instance: 410/3sat_12.cnf
```

这个结果偏弱：固定 early-trace selector 在 expanded first-15 上仍只有一个 hit。下一步不应直接扩全 49 个 selector run，而应先做 expanded oracle sampling 诊断，判断是 selector failure 还是 sampled March policy 本身在 both-unknown set 上 oracle solves 稀少。

### 6. Residual portfolio 顶会主线

当前可防守主线已经锁定为：

```text
March + CaDiCaL union failed residual setting
-> fixed selected neural restart portfolio
vs fixed same-budget non-neural rerun portfolio
```

关键约束：

- oracle sampling 只做 checkpoint diagnostic / upper bound，不作为 paper claim。
- all-49 both-unknown 只做 go/no-go gate，不作为最终主结果。
- dev / held-out 必须在数据生成或 residual split 阶段锁死；held-out 只做 one-shot evaluation。
- adaptive top-k、probe thresholds、solver/config cycle 必须 dev-only 预注册。
- 同预算 non-neural control 是必须项，并且必须计入 neural generation、probe、full-run、wall-clock 和 allocated residual CPU budget。

`ResidualProxyCap10/last.pt` 的 all-49 oracle diagnostic 已完成：

```text
checkpoint: runs/GNN_March_3SAT_ResidualProxyCap10/last.pt
out_dir: runs/analysis/benchmark_march_expanded_sample_portfolio_oracle_residual_proxy_cap10_iter0
sample_seed: 1729
num_samples: 16
full_cpu_lim: 60
```

最终 gate 结果：

```text
completed: 49 / 49
oracle_solved: 1
solved: 410/3sat_12.cnf, solved_samples=8/16, best_time=10.875, best_sample_id=5
decision: fail
```

正式 artifact：

- `runs/analysis/benchmark_march_expanded_sample_portfolio_oracle_residual_proxy_cap10_iter0/instance_oracle_summary.csv`
- `docs/benchmark_march_expanded_sample_portfolio_oracle_residual_proxy_cap10_iter0.md`
- `docs/residual_portfolio_gate_decision_residual_proxy_cap10_iter0.md`

结论：该 checkpoint 没有通过 `oracle_solved >= 5/49` 的继续门槛，必须停止
selector 调参，不进入 dev-only selector freeze / held-out same-budget control。
下一步应回到 residual-targeted / diversity / entropy 训练目标，产生新
checkpoint 后再跑同样的 oracle gate。

`ResidualTargetedIter22/last.pt`、`ResidualCoverageDiverseBestIter2/best.pt`、
`ResidualEliteReplayCoverageDiverseBestIter2/best.pt` 和
`ResidualProgressDiverse/best.pt` 都已经失败同一 all-49 oracle gate，不能进入
selector freeze 或 held-out same-budget control。最新正式 gate 是
`ResidualProgressDiverse`：

```text
checkpoint: runs/GNN_March_3SAT_ResidualProgressDiverse/best.pt
sha256: f9ac184722fe5785c3b084c2e173e8d799ae13a7d2b1a151887e66d4d662997a
decision: fail
total: 49
oracle_solved: 1
positives:
  - 410/3sat_12.cnf, solved_samples=8/16, best_time=6.5103, best_sample_id=2
```

Artifacts:

- `runs/analysis/benchmark_march_expanded_sample_portfolio_oracle_residual_progress_diverse/instance_oracle_summary.csv`
- `runs/analysis/benchmark_march_expanded_sample_portfolio_oracle_residual_progress_diverse/raw_samples_all.csv`
- `docs/benchmark_march_expanded_sample_portfolio_oracle_residual_progress_diverse.md`
- `docs/residual_portfolio_gate_decision_residual_progress_diverse.md`
- `runs/analysis/benchmark_transition_band_residual_large/residual_portfolio_gate_decision_residual_progress_diverse.json`

`ResidualProgressDiverse` training provenance:

```text
config: configs/config_train_rlaf_march_residual_progress_diverse.yaml
model_dir: runs/GNN_March_3SAT_ResidualProgressDiverse
from_checkpoint: runs/GNN_March_3SAT_ResidualEliteReplayCoverageDiverseBestIter2/best.pt
target_stat: composite_progress_diverse
training process: complete
optimized train iterations logged: 24
dev validation iterations logged: 11
best score iteration: 12
best score: 4.315622056940805
last checkpoint sha256: 826c2d87be226aeb238eb3deca61f12876858db012e597704354fb86ec5dd7b5
```

`run_march_sample_portfolio_multiseed.py` now locks each `--out-dir` while it
writes raw/summary/global artifacts, preventing concurrent runner pollution in
the same namespace.

Consequence:

```text
Stop selector work for runs/GNN_March_3SAT_ResidualProgressDiverse/best.pt.
Do not enter dev-only selector freeze or held-out same-budget control.
Do not rerun solved-first/progress-diverse GRPO as-is; it reduced all-49
coverage to the single recurring 410/3sat_12.cnf positive.
```

Current next model-side branch should be coverage-first residual supervision:

```text
residual_train/dev multi-seed mining
-> coverage-balanced elite/contrastive manifest
-> supervised residual policy finetune with KL to source checkpoint
-> unchanged all-49 oracle gate
```

Rationale: existing residual train/dev mining for
`ResidualCoverageDiverseBestIter2` already found 30 train positive instances and
7 dev positive instances, including size-440 positives. The failed replay branch
only made a light probability update to mined elites and did not improve the
all-49 diagnostic. The next objective should therefore optimize instance
coverage and contrast solved samples against failed samples from the same CNF,
not just clone fastest elites or reward generic progress counters.

Implemented first-pass utilities:

- `build_residual_contrastive_replay_manifest.py`
- `train_residual_contrastive_replay.py`
- `tests/test_residual_contrastive_replay.py`

Formal contrastive manifests have been built from the existing
`ResidualCoverageDiverseBestIter2` residual train/dev mining artifacts:

```text
train manifest:
  path: runs/analysis/benchmark_transition_band_residual_large/residual_train_contrastive_replay_manifest_coverage_diverse_best_iter2.csv
  rows: 156
  positive contrastive instances: 27
  by size: 410=12, 425=9, 440=6

dev manifest:
  path: runs/analysis/benchmark_transition_band_residual_large/residual_dev_contrastive_replay_manifest_coverage_diverse_best_iter2.csv
  rows: 30
  positive contrastive instances: 6
  by size: 410=2, 440=4
```

Verification:

```text
py_compile passed for the two new scripts and test file
unittest tests.test_residual_contrastive_replay tests.test_residual_elite_replay tests.test_residual_training_objective: 28 tests OK
row-limited CPU smoke: runs/analysis/tmp_residual_contrastive_replay_smoke
```

The smoke checkpoint is not formal and must not be gated.

The full first-pass contrastive run has completed:

```text
model_dir: runs/GNN_March_3SAT_ResidualContrastiveReplayCoverageDiverseBestIter2
source checkpoint: runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt
train manifest: residual_train_contrastive_replay_manifest_coverage_diverse_best_iter2.csv
dev manifest: residual_dev_contrastive_replay_manifest_coverage_diverse_best_iter2.csv
epochs: 8
best epoch: 7
best dev score: -0.727973997592926
best checkpoint sha256: 56dba0670da653bea7a8106c5db2ca34463928bd8f13c5bb302dd47da313562c
last checkpoint sha256: c56fd8f865c65aca9d3a1f7d7e4837e4425eec526b3d0c57a68186623ce17cd9
config sha256: 53fede17e28f0f40a3e3fd871ef05b1d14a780038cd640e2adfa4c84266e1d53
metrics sha256: c8967d8a1ee64b08edf605c2069365ec10639710e2595c4f166806b324734c24
```

Metric caveat: dev loss improved mostly through lower signed BCE/log-prob terms
while pairwise loss stayed around `0.69`; positive and negative log-probs both
declined. This checkpoint is a legitimate next oracle diagnostic candidate, but
not yet evidence that the contrastive loss has fixed residual coverage.

The unchanged all-49 oracle gate for this contrastive checkpoint is complete
and failed:

```text
gate: residual_contrastive_replay_coverage_diverse_best_iter2_all49
checkpoint: runs/GNN_March_3SAT_ResidualContrastiveReplayCoverageDiverseBestIter2/best.pt
checkpoint sha256: 56dba0670da653bea7a8106c5db2ca34463928bd8f13c5bb302dd47da313562c
decision: fail
total: 49
oracle_solved: 2
positives:
  - 410/3sat_12.cnf, solved_samples=7/16, best_time=10.5340, best_sample_id=11
  - 425/3sat_28.cnf, solved_samples=1/16, best_time=50.6457, best_sample_id=10
```

Artifacts:

- `runs/analysis/benchmark_march_expanded_sample_portfolio_oracle_residual_contrastive_replay_coverage_diverse_best_iter2/instance_oracle_summary.csv`
- `docs/benchmark_march_expanded_sample_portfolio_oracle_residual_contrastive_replay_coverage_diverse_best_iter2.md`
- `docs/residual_portfolio_gate_decision_residual_contrastive_replay_coverage_diverse_best_iter2.md`
- `runs/analysis/benchmark_transition_band_residual_large/residual_portfolio_gate_decision_residual_contrastive_replay_coverage_diverse_best_iter2.json`

Consequence: this recovers the two recurring positives but still has `0/30`
size-440 coverage and fails the pre-registered `fail_max=2` gate. Do not enter
selector/protocol freeze or held-out same-budget control. Next model-side step
must fix the contrastive loss sign/normalization or expand residual train/dev
mining seeds; do not rerun the same contrastive objective as-is.

已经加固 same-budget non-neural control：

- `build_non_neural_schedule_from_neural_budget.py` 现在记录 `attempt_limit` 和
  `schedule_mode=dev_budget_rule`，dev artifact 冻结 solver/config cycle。
- `run_residual_non_neural_budget_control.py` 支持
  `--neural-budget-summary`，在 held-out 上按每个实例的 neural
  `total_cpu_allocated` 展开 frozen solver cycle，生成 per-instance same-budget
  non-neural schedule。
- runner 会拒绝 `--schedule-csv` 和输出 `schedule.csv` 使用同一路径，避免
  frozen source artifact 被 run artifact 覆盖。
- `audit_residual_portfolio_protocol.py` 现在检查 per-instance budget equality，
  并能从 frozen `solver_cycle + attempt_limit` 复算每个 held-out instance 的
  non-neural schedule。
- `decide_residual_portfolio_gate.py` 现在支持 `--checkpoint`，gate decision
  文档会记录 oracle CSV SHA256、checkpoint 路径和 checkpoint SHA256，避免
  gate 结论与模型版本脱钩。
- `decide_residual_portfolio_gate.py` formal mode is fail-closed: it requires
  `len(instance_oracle_summary) == --expected-total`, rejects duplicate
  instance keys, and strictly parses `solved_any` so string `False` is not
  counted as solved. `--allow-diagnostic-total` is only for non-formal
  monitoring summaries.
- `summarize_residual_portfolio_paper_table.py` 现在报告
  `same_budget_max_per_instance_diff` 和 `same_budget_mean_per_instance_diff`，
  不再只依赖均值预算对齐；并且严格解析 solve boolean、拒绝重复
  oracle/non-neural instance keys，避免 string `False` 或重复行夸大 final
  solve counts。
- `audit_residual_portfolio_protocol.py` 现在在 held-out audit 中检查 neural
  group-key uniqueness、non-neural instance-key uniqueness、fixed selector
  provenance 和 per-instance same-budget equality。
- `audit_residual_portfolio_protocol.py` 的 final gate-record audit 现在会回读
  gate JSON 引用的 oracle CSV、checkpoint 和 replay training-config audit，
  复核 artifact 存在性、SHA256、oracle denominator/solved count、oracle
  checkpoint provenance、formal replay audit checks 和 failure count，避免只信
  手写 gate JSON 字段。
- 新增/更新测试在 `tests/test_residual_portfolio_protocol.py`，验证 per-instance
  budget schedule、CaDiCaL variant provenance、selector spec dev hash、schedule
  source split/hash、gate provenance hash、paper-table per-instance budget diff
  等协议约束。

## 改了哪些文件

### March weighted solver

为支持 probe/runtime audit，`march_weighted` 已加入内部 CPU budget：

- `solvers/march_weighted/common.h`
- `solvers/march_weighted/march.c`
- `solvers/march_weighted/solver.c`

功能：

- 支持 `--cpu-lim=<seconds>`
- 内部超时返回 `UNKNOWN`
- probe timeout 仍输出 March counters，避免只依赖 Python external kill
- 已 rebuild `solvers/march_weighted/march_nh`

### Solver wrapper

- `src/solving/solver.py`

功能：

- weighted March 调用时传入 `--cpu-lim`
- 解析 March counters：
  - `dead_ends_in_main`
  - `lookAheadCount`
  - `unitResolveCount`
  - `necessary_assignments`
  - `bin_sat`
  - `bin_unsat`
  - `decisions`
  - `CPU time`

### 当前 March sampled guidance / gate 脚本

- `run_transition_band_expanded_gate.py`
- `run_march_expanded_early_trace_gate.py`
- `run_march_early_trace_selector.py`
- `run_march_budgeted_sample_selector.py`
- `run_march_sample_portfolio_triage.py`
- `run_march_sample_portfolio_multiseed.py`
- `analyze_march_sample_selector_budget.py`
- `analyze_march_sample_selector_features.py`
- `analyze_march_learned_sample_selector.py`

### 重要文档

- `docs/top_conference_model_gate_next_steps.md`
- `docs/benchmark_transition_band_expanded_gate.md`
- `docs/benchmark_march_expanded_early_trace_gate.md`
- `docs/benchmark_march_early_trace_selector.md`
- `docs/benchmark_march_budgeted_sample_selector.md`
- `docs/benchmark_march_sample_selector_budget.md`
- `docs/benchmark_march_learned_sample_selector.md`
- `docs/benchmark_march_guidance_transition_full.md`
- `docs/benchmark_march_guidance_transition_full_overlap.md`

### 重要数据/结果目录

- `data/benchmark_transition_band_expanded/`
- `data/benchmark_march_expanded_early_trace_gate/`
- `runs/analysis/benchmark_transition_band_expanded/`
- `runs/analysis/benchmark_march_expanded_early_trace_gate/`
- `runs/analysis/benchmark_march_early_trace_selector/`
- `runs/analysis/benchmark_march_budgeted_sample_selector/`
- `runs/analysis/benchmark_march_learned_sample_selector/`

### 旧 Glucose/Online 线相关文件

这些文件很多仍在工作区，保留即可，不要清理或回滚：

- `evaluate_guided_solver.py`
- `src/model/model.py`
- `src/data/dataset.py`
- `src/policy/evaluate.py`
- `src/policy/policy.py`
- `train_rlaf.py`
- `train_supervised.py`
- 大量 `configs/config_eval_guided_solver_*`
- 大量 `docs/paper_*`、`docs/*selector*`、`runs/analysis/*`

它们是历史实验资产，但当前顶会实验重点不是继续调这条线。

## 当前分支、最近 commit、git status

当前分支：

```text
codex/enhanced-model-v1
```

最近 commit：

```text
6bf1bb8 Add repeated 3SAT-450 strong solver gate
```

当前 `git status --short`：

- 工作区非常 dirty。
- tracked modified 包括：
  - `README.md`
  - `build_solvers.sh`
  - `configs/config_eval_guided_solver.yaml`
  - `configs/config_train_rlaf.yaml`
  - `configs/config_train_supervised.yaml`
  - `docs/benchmark_3sat450_gate.md`
  - `evaluate_guided_solver.py`
  - `figures/fig_portfolio_full400_paper.pdf`
  - `figures/fig_portfolio_full400_paper.svg`
  - `figures/make_portfolio_results_paper.py`
  - `run_e2e_local5_cadical55_portfolio.py`
  - `solvers/glucose_weighted/core/Solver.cc`
  - `solvers/glucose_weighted/core/Solver.h`
  - `solvers/glucose_weighted/simp/Main.cc`
  - `solvers/march_weighted/common.h`
  - `solvers/march_weighted/march.c`
  - `solvers/march_weighted/solver.c`
  - `src/data/dataset.py`
  - `src/model/model.py`
  - `src/policy/evaluate.py`
  - `src/policy/policy.py`
  - `src/solving/solver.py`
  - `train_rlaf.py`
  - `train_supervised.py`
  - `verify_paper_claims.py`
- untracked 很多，包括：
  - `PROJECT_CONTEXT.md`
  - March gate runners / analysis scripts
  - many `configs/config_*`
  - many `docs/*`
  - `data/test/`, `data/benchmark_*`, `data/counterfactual_trace/`
  - `runs/GNN_*`, `runs/analysis/*`
  - built solver binaries/objects under `solvers/`
  - `paper/`, `figures/*`, `wandb/`

注意：不要因为 dirty 就 reset 或 checkout。这里面大部分是已有实验资产和用户/前序代理产物。

## 跑过哪些测试，结果如何

### 代码级检查

已跑过：

```bash
python -m py_compile run_transition_band_expanded_gate.py run_march_expanded_early_trace_gate.py run_march_early_trace_selector.py src/solving/solver.py
```

结果：通过。

已跑过：

```bash
python -m py_compile run_march_early_trace_selector.py analyze_march_learned_sample_selector.py
```

结果：通过。

早期 Glucose/Online 线还跑过：

```bash
python3 -m unittest tests.test_event_adapter tests.test_local_reopen_override_export
```

结果：`Ran 22 tests ... OK`。

### Strong solver gate

已跑过：

```bash
python run_transition_band_expanded_gate.py \
  --sizes 410 425 440 \
  --instances 50 \
  --workers 8
```

结果：

```text
March/CaDiCaL both-unknown total: 49
410: 5 / 50
425: 14 / 50
440: 30 / 50
```

### Expanded early-trace smoke

已跑过：

```bash
python run_march_expanded_early_trace_gate.py \
  --limit-instances 5 \
  --sample-seeds 1729 \
  --num-samples 8 \
  --top-k 2 \
  --probe-cpu-lim 1.0 \
  --policy probe_solved_then_high_deadends \
  --resume
```

结果：

```text
solved: 1 / 5
solved instance: 410/3sat_12.cnf
```

当前 `limit-instances=15` run 已完成。结果是：

```text
completed: 15 / 15
solved: 1 / 15
solved instance: 410/3sat_12.cnf
```

## 下一步应该从哪里继续

### 立即继续

1. 确认没有遗留运行进程，并保留 15-instance 结果。

```bash
find runs/analysis/benchmark_march_expanded_early_trace_gate/groups -name '*top2_probe1p0_summary.csv' | wc -l
```

2. 汇总 15-instance 结果：

```bash
python - <<'PY'
import glob
import pandas as pd

frames = []
for p in glob.glob('runs/analysis/benchmark_march_expanded_early_trace_gate/groups/*top2_probe1p0_summary.csv'):
    df = pd.read_csv(p)
    df['path'] = p
    frames.append(df)

s = pd.concat(frames, ignore_index=True)
cols = ['size', 'file_key', 'sample_seed', 'solved_any_strict60', 'total_cpu_capped']
print(s[cols].sort_values(['size', 'file_key']).to_string(index=False))
print('solved', int(s.solved_any_strict60.sum()), '/', len(s))
print(s[s.solved_any_strict60][cols + ['path']].to_string(index=False))
PY
```

### 根据 15-instance 结果决策

由于 15 个里只有 `410/3sat_12.cnf` 一个 hit，不建议直接扩到全 49 个同配置 selector run。下一步先做 expanded oracle sampling 诊断：

```bash
# 设计一个只评估 oracle sampled solves 的 expanded run:
# 1 seed, 16 samples, no selector tuning.
# 目标是判断 March sampled guidance 在 both-unknown set 上是否有足够 oracle positives.
```

建议口径：

- 先用 first-15 或 all-49 both-unknown 做 1 seed x 16 samples 的 oracle diagnostic。
- 只统计是否存在 any sampled solve，不调 selector。
- 如果 oracle solves 存在但 `probe_solved_then_high_deadends` 找不到，再研究 selector。
- 如果 oracle solves 也稀少，转向 retrain March policy objective，目标是 strong-union-unsolved instances。

### 顶会硬 gate

要支撑顶会，至少需要满足：

- strong baseline 是 March/CaDiCaL union，不是 Glucose default。
- neural-only solves 在 expanded held-out both-unknown set 上非零且可复现。
- fixed selector top-k 能 recover oracle sampled solves，而不是事后挑。
- wall-clock budget 不能明显输给简单 rerun strong solver。
- learned selector 若要作为贡献，必须在 held-out split 上超过 simple early-trace baseline。

## 哪些坑不要重复踩

- 不要把旧 Glucose/Online-Consistent/Local Boundary Correction 重新包装成顶会性能主线。
- 不要继续调 polarity / SBE / pairwise veto / compact-stable 这类旧分支。
- 不要把 oracle sampled solve 写成 deployable method。
- 不要在 focused 2-instance 结果上做大 claim。
- 不要为了救结果在 expanded set 上反复 hand-tune selector；先区分 oracle scarcity 还是 selector failure。
- 不要把 `same-seed repeated runtime` 混成 solver-seed robustness。
- 不要忽略 March/CaDiCaL union baseline；只赢 one-shot neural guidance 没有顶会说服力。
- 不要直接清理 dirty worktree；里面有大量实验资产。
- 不要在没有 `--resume` 和 per-group artifacts 的情况下开长跑。
- 不要把 checkpoint 纳入普通 git；大模型/大 checkpoint 需要 Git LFS 或外部 artifact 单独决定。

## 2026-05-31 方案可行性评估更新

当前最可行的顶会主线是 residual portfolio，而不是继续修补旧
Glucose/Online 主线：

```text
March + CaDiCaL union failed residual setting
fixed selected neural restart portfolio
vs fixed same-budget non-neural rerun portfolio
```

这条主线的可防守点：

- 强 baseline 足够正面：神经方法只处理 March/CaDiCaL 都未解出的 residual instances。
- oracle 与主 claim 分离：oracle sampling 只作为 checkpoint / distribution potential diagnostic。
- dev / held-out 分离必须从 candidate generation 阶段锁死，residual split 从 candidate split 投影。
- adaptive top-k 只允许在 dev 上确定阈值和规则，held-out 一次性冻结评估。
- same-budget non-neural rerun control 是必须项，不能只和 single-run March/CaDiCaL 比。
- 预算报告必须包括 GNN/sample generation、probe、full-run 的 CPU 和 wall-clock 开销。

已新增代码级护栏：

- `run_march_early_trace_selector.py` 记录
  `neural_generation_wall_time`、`probe_wall_time_total`、
  `full_wall_time_total`、`total_wall_time`。
- `run_march_expanded_early_trace_gate.py` 的 selector spec 和文档同步记录 wall-clock budget accounting。
- `run_march_expanded_early_trace_gate.py` / `run_march_early_trace_selector.py`
  显式记录 `probe_solved_cap`，默认值 1，避免 adaptive selector 的
  “probe-solved first” 分支没有 frozen cap 证据。
- `audit_residual_portfolio_protocol.py` 现在要求 held-out neural summary 暴露 CPU 与 wall-clock budget 字段。
- `audit_residual_portfolio_protocol.py` 现在要求 held-out selector spec
  来自 dev spec，并校验 `selector_spec_source_split=dev` 与 dev spec
  SHA256；也要求 non-neural schedule 来自 dev neural summary，并校验
  `source_split=dev` 与 dev summary SHA256。
- `build_non_neural_schedule_from_neural_budget.py` 现在写入
  `source_split`、`neural_summary_sha256`、可选 `selector_spec_sha256`，
  并支持固定 solver/config cycle。
- `run_residual_non_neural_budget_control.py` 现在支持 CaDiCaL 固定
  seed/config variants：`cadical_seed1/2/3`、`cadical_plain_seed1/2`、
  `cadical_sat_seed1`、`cadical_unsat_seed1`、
  `cadical_shuffle_seed1/2`。当前 unweighted March binary 没有暴露
  random seed，因此不要把重复 March 默认运行称为独立 seed rerun。
- `summarize_residual_portfolio_paper_table.py` 现在把 neural/non-neural wall-clock budget 汇入 denominator-preserving table。
- `finalize_residual_large_gate.py` 现在会在 strict summary、residual split
  和 protocol audit 后自动运行 `summarize_residual_portfolio_paper_table.py`，
  生成 `residual_portfolio_paper_table_split_seed1729.csv` 与对应文档骨架。

验证：

```bash
/home/sunshixin/anaconda3/envs/rlaf/bin/python -m py_compile \
  run_march_early_trace_selector.py \
  run_march_expanded_early_trace_gate.py \
  audit_residual_portfolio_protocol.py \
  summarize_residual_portfolio_paper_table.py
```

通过。用旧 tmp held-out artifact 做审计 smoke 时，因缺少 wall-clock
字段被正确标 fail，说明最终协议会拦住“只报 solver CPU”的不完整结果。

新增验证：

```bash
/home/sunshixin/anaconda3/envs/rlaf/bin/python -m unittest \
  tests.test_residual_portfolio_protocol
```

通过，覆盖 dev-derived non-neural schedule、CaDiCaL variant 命令生成、
selector spec dev-source/hash 审计。

## 2026-06-01 residual large gate / training 状态

`benchmark_transition_band_residual_large` 的 strong gate 已完成并已
finalize。不要重启 large gate，也不要重复 finalization，除非明确要重建
同一批 artifact。

最终 strict-60 denominator：

```text
candidate total: 900
March strict solved: 518
CaDiCaL strict solved: 364
union solved: 550
both-unknown residual: 350
late March solves after nominal 60s: 34 reported separately, not counted solved
```

关键产物：

- `runs/analysis/benchmark_transition_band_residual_large/combined.csv`
- `runs/analysis/benchmark_transition_band_residual_large/summary.csv`
- `runs/analysis/benchmark_transition_band_residual_large/solver_overlap.csv`
- `runs/analysis/benchmark_transition_band_residual_large/both_unknown_subset.csv`
- `runs/analysis/benchmark_transition_band_residual_large/residual_split_seed1729/manifest.csv`
- `runs/analysis/benchmark_transition_band_residual_large/protocol_audit_split_seed1729.csv`
- `runs/analysis/benchmark_transition_band_residual_large/residual_training_ready_audit_seed1729.csv`
- `runs/analysis/benchmark_transition_band_residual_large/residual_portfolio_paper_table_split_seed1729.csv`

Residual split 从预注册 candidate split 投影，pilot all-49 已按 CNF hash
排除：

```text
residual_train: 168
residual_dev: 93
residual_heldout: 89
```

Protocol audit 和 training-ready audit 均通过。paper table skeleton 已生成，
neural/non-neural held-out 结果仍是 `not_run`，这是当前正确状态。

Residual-targeted training 已启动。注意不要再启动第二个写同一目录的训练。

已完成：

- preflight 通过：加载 residual train/dev、兼容加载
  `runs/GNN_March_3SAT/best.pt`、March 采样求解和 GRPO 单步更新正常。
- 一次交互式正式训练在被中断前完成 initial validation 和 iteration 0，
  写出了 `runs/GNN_March_3SAT_ResidualTargeted/best.pt` 与 `last.pt`。
- 已修复训练 resume 的 best checkpoint 风险：`train_rlaf.py` 现在会把
  validation best score 写入 `best_score.json`，resume 时读取该 sidecar。
  这样不会因为新进程里 `best_score=inf` 而无条件覆盖已有 `best.pt`。
- 新增 `score_rlaf_checkpoint.py`，可用训练验证协议给 checkpoint 重算
  dev score，并可写 `best_score.json`。
- 已对当前 `best.pt` 重算 residual_dev composite 分数：
  `10.465713493718855`。产物：
  `runs/GNN_March_3SAT_ResidualTargeted/best_score.json`
  和
  `runs/analysis/benchmark_transition_band_residual_large/residual_targeted_best_dev_score.csv`。
- 重要：`runs/GNN_March_3SAT_ResidualTargeted/best.pt` 仍不能作为 oracle
  gate 候选；它是在最新 resume optimizer step 之前写出的旧 best。
- full-60s resume 已完成多轮真实 GRPO 更新，并在 iteration 23 的
  validation/rollout 后被手动 SIGTERM 停止以释放 March workers 跑 gate：
  - log: `runs/analysis/benchmark_transition_band_residual_large/logs/residual_targeted_training_resume.log`
- frozen checkpoint for official gate:
  `runs/GNN_March_3SAT_ResidualTargetedIter22/last.pt`
- checkpoint sha256:
  `4cf7537b86c86d8caec832d064ee4704388ec881874d30950930d832fa329058`
- older frozen checkpoints retained for provenance:
  `runs/GNN_March_3SAT_ResidualTargetedIter0/last.pt` and
  `runs/GNN_March_3SAT_ResidualTargetedIter8/last.pt`

`ResidualTargetedIter22/last.pt` 的 all-49 oracle diagnostic 已完成：

```text
checkpoint: runs/GNN_March_3SAT_ResidualTargetedIter22/last.pt
sample_seed: 1729
num_samples: 16
full_cpu_lim: 60
total: 49
oracle_solved: 2
decision: fail
```

Oracle positives:

```text
410/3sat_12.cnf: solved_samples=6/16, best_time=1.0505, best_sample_id=11
425/3sat_28.cnf: solved_samples=1/16, best_time=59.2371, best_sample_id=3
```

Artifacts:

- `runs/analysis/benchmark_march_expanded_sample_portfolio_oracle_residual_targeted_iter22/instance_oracle_summary.csv`
- `docs/benchmark_march_expanded_sample_portfolio_oracle_residual_targeted_iter22.md`
- `docs/residual_portfolio_gate_decision_residual_targeted_iter22.md`

Protocol consequence:

```text
Stop selector work for runs/GNN_March_3SAT_ResidualTargetedIter22/last.pt.
Do not enter dev-only selector freeze or held-out same-budget non-neural control for this checkpoint.
The next step is model-side objective change, not top-k/dead_ends selector tuning.
```

判据保持不变：

- oracle `<=2/49`：不要救 selector，继续改 residual training objective。
- oracle `3-4/49`：边际，扩大 residual pilot 或改训练目标。
- oracle `>=5/49`：进入 dev-only selector 阈值/top-k/schedule 冻结，再做
  held-out fixed neural vs same-budget non-neural portfolio。

不要继续重启同一个 solved-first `ResidualTargeted` 配置；Iter22 已经说明该
目标下 oracle coverage 只有 `2/49`。第一版模型侧 coverage/diversity 目标
已经完成并失败：

```text
configs/config_train_rlaf_march_residual_coverage_diverse.yaml
runs/GNN_March_3SAT_ResidualCoverageDiverse
from_checkpoint=runs/GNN_March_3SAT_ResidualTargetedIter22/last.pt
target_stat=composite_diverse
cnf_per_iter=8, num_samples=8, March cpu-lim=20
```

`composite_diverse` 保留 solved-first composite cost，但对同一 CNF 内
unsolved 且彼此相似的 sampled weight vectors 加 cost，并在 GRPO 中加入很小
entropy bonus。目的不是救 selector，而是提高 fixed sample budget 下的
oracle coverage。

训练已完整跑完 16 iterations；dev composite 选择的 best checkpoint 和最终
last checkpoint 已冻结：

```text
runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt
sha256: c2b1b7d543e311f48bba393d81e9cf41d9615949426552e1ad5fc13b377e9f5f
best_score: 8.904377399524758
best iteration: 2

runs/GNN_March_3SAT_ResidualCoverageDiverseFinalIter15/last.pt
sha256: 9fe407aca77ceb4169834aa57815f3b55053f37effe34fb650c0de75abdfd296
```

只对 dev 选出的 best checkpoint 跑了 all-49 oracle gate，避免用 oracle 在
best/last 之间事后选 checkpoint：

```text
gate: residual_coverage_diverse_best_iter2_all49
checkpoint: runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt
total: 49
oracle_solved: 2
decision: fail
source sha256: 8dca7175f0c6e700606981083a8074cfef7f7aa8db2006c7ce32fc393118a3bd
```

Oracle positives:

```text
410/3sat_12.cnf: solved_samples=9/16, best_time=1.4119, best_sample_id=15
425/3sat_28.cnf: solved_samples=1/16, best_time=59.8441, best_sample_id=15
```

Artifacts:

- `runs/analysis/benchmark_march_expanded_sample_portfolio_oracle_residual_coverage_diverse_best_iter2/instance_oracle_summary.csv`
- `docs/benchmark_march_expanded_sample_portfolio_oracle_residual_coverage_diverse_best_iter2.md`
- `docs/residual_portfolio_gate_decision_residual_coverage_diverse_best_iter2.md`

Protocol consequence:

```text
Stop selector work for runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt.
Do not enter dev-only selector freeze or held-out same-budget non-neural control.
The next step is a stronger model-side objective change, not selector/top-k/dead_ends tuning.
```

如果 diversity variant 无法完成 optimizer step，再使用 staged
residual-targeted fallback：

```text
configs/config_train_rlaf_march_residual_targeted_stage1.yaml
runs/GNN_March_3SAT_ResidualTargetedStage1
cnf_per_iter=8, num_samples=8, March cpu-lim=20
```

Stage1 使用相同 residual train/dev split 和 composite solved-first objective，
但单轮 rollout 成本更低，目标是先获得一个确实完成 GRPO 更新的 residual
checkpoint。只有日志出现 `Optimized model for ...` 且 `last.pt` mtime 更新后，
才允许对该 checkpoint 跑同样的 all-49 oracle gate；否则不能进入 selector
或 paper-result 协议。

Stage1 gate 必须使用独立 artifact namespace，例如：

```text
runs/analysis/benchmark_march_expanded_sample_portfolio_oracle_residual_targeted_stage1
docs/benchmark_march_expanded_sample_portfolio_oracle_residual_targeted_stage1.md
docs/residual_portfolio_gate_decision_residual_targeted_stage1.md
```

如果 Stage1 还没有 validation 写出 `best.pt`，可 gate
`runs/GNN_March_3SAT_ResidualTargetedStage1/last.pt`，但 gate decision 必须
记录 exact checkpoint path 和 checkpoint hash。不要把 Stage1 artifact 与
`ResidualTargeted` 或 `ResidualProxyCap10` 混用。

## 2026-06-02 Elite Replay / Hard-Positive Finetuning 更新

当前失败模式仍是 oracle scarcity，不是 selector failure：

```text
ResidualTargetedIter22 all-49 oracle_solved=2/49
ResidualCoverageDiverseBestIter2 all-49 oracle_solved=2/49
```

因此下一步不应调 `top-k`、`dead_ends` 或 learned selector，而应显式增加
已解 residual sampled restarts 的概率质量。已经新增两段可复用代码：

- `build_residual_elite_replay_manifest.py`
  - 从 sampled March raw artifacts 中筛 solved samples。
  - 记录 `sample_seed`、`sample_id`、`num_samples_generated`、checkpoint hash、
    raw CSV hash、split/cnf path。
  - 每个 instance 只保留最快的 `max_per_instance` 个 elite samples。
- `train_residual_elite_replay.py`
  - 从 checkpoint + `sample_seed` + `sample_id` 确定性重建 elite
    `var_params`。
  - 训练目标是提高 elite `log_prob`，并用 KL penalty 约束到 source
    checkpoint。
  - 保存 `config.yaml`、`best.pt`、`last.pt` 和 `metrics.csv`，后续仍可用
    现有 `load_checkpoint(..., var_output=True)` 进入 all-49 gate。

已验证：

```bash
env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python -m py_compile \
  build_residual_elite_replay_manifest.py \
  train_residual_elite_replay.py \
  tests/test_residual_elite_replay.py

env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python -m unittest \
  tests.test_residual_elite_replay \
  tests.test_residual_training_objective \
  tests.test_residual_portfolio_protocol
```

结果：

```text
13 tests OK
```

Smoke 只用既有 all-49 `ResidualTargetedIter22` raw artifact 验证 replay
管线，不作为正式训练数据：

```text
runs/analysis/benchmark_transition_band_residual_large/residual_targeted_iter22_elite_replay_smoke_manifest.csv
docs/residual_targeted_iter22_elite_replay_smoke_manifest.md
elite_rows=5
positive_instances=2
runs/GNN_March_3SAT_ResidualEliteReplaySmoke/
```

`ResidualEliteReplaySmoke` 只跑了 `limit_train_rows=2, epochs=1, device=cpu`，
用于验证 deterministic reconstruction、log-prob objective 和 checkpoint
保存。不要 gate 这个 smoke checkpoint。

正式方向是先在 residual train/dev split 上挖 positives，再训练 replay：

```text
source checkpoint:
runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt
sha256: c2b1b7d543e311f48bba393d81e9cf41d9615949426552e1ad5fc13b377e9f5f

train mining namespace:
runs/analysis/benchmark_march_residual_train_elite_mining_coverage_diverse_best_iter2
data/benchmark_march_residual_train_elite_mining_coverage_diverse_best_iter2
docs/benchmark_march_residual_train_elite_mining_coverage_diverse_best_iter2.md
```

Current progress of this train-mining namespace:

```text
completed residual_train instances: 23 / 168
3sat/410/3sat_101.cnf: solved_samples=0/16
3sat/410/3sat_102.cnf: solved_samples=0/16
3sat/410/3sat_105.cnf: solved_samples=0/16
3sat/410/3sat_117.cnf: solved_samples=0/16
3sat/410/3sat_122.cnf: solved_samples=2/16, best_time=56.9111, best_sample_id=5
3sat/410/3sat_13.cnf: solved_samples=15/16, best_time=55.4571, best_sample_id=2
3sat/410/3sat_135.cnf: solved_samples=0/16
3sat/410/3sat_136.cnf: solved_samples=0/16
3sat/410/3sat_155.cnf: solved_samples=0/16
3sat/410/3sat_159.cnf: solved_samples=0/16
3sat/410/3sat_160.cnf: solved_samples=7/16, best_time=54.9684, best_sample_id=14
3sat/410/3sat_166.cnf: solved_samples=0/16
3sat/410/3sat_172.cnf: solved_samples=3/16, best_time=58.4589, best_sample_id=2
3sat/410/3sat_19.cnf: solved_samples=0/16
3sat/410/3sat_191.cnf: solved_samples=0/16
3sat/410/3sat_213.cnf: solved_samples=0/16
3sat/410/3sat_216.cnf: solved_samples=13/16, best_time=57.7088, best_sample_id=9
3sat/410/3sat_226.cnf: solved_samples=0/16
3sat/410/3sat_231.cnf: solved_samples=0/16
3sat/410/3sat_235.cnf: solved_samples=8/16, best_time=58.1850, best_sample_id=5
3sat/410/3sat_247.cnf: solved_samples=7/16, best_time=54.7944, best_sample_id=14
3sat/410/3sat_261.cnf: solved_samples=0/16
3sat/410/3sat_269.cnf: solved_samples=0/16
partial elite manifest:
runs/analysis/benchmark_transition_band_residual_large/residual_train_elite_replay_manifest_coverage_diverse_best_iter2_partial.csv
elite_rows=6
latest progress summary:
runs/analysis/benchmark_transition_band_residual_large/residual_train_elite_mining_progress_coverage_diverse_best_iter2.csv
docs/residual_train_elite_mining_progress_coverage_diverse_best_iter2.md
```

A long residual-train mining run has been started outside the sandbox so it can
continue after the Codex turn:

```text
pid: 2214783
log:
runs/analysis/benchmark_transition_band_residual_large/logs/residual_train_elite_mining_coverage_diverse_best_iter2.log
```

It uses `artifact-mode instance`, so completed instance artifacts are reusable.
Do not start any other March-heavy training/gate job while this is running.
Current decision:

```text
positive_instances=7
solved_samples=55
min_positive_instances_for_replay=8
positive_floor_met=false
complete_mining=false
decision=continue_mining
```

`build_residual_elite_replay_manifest.py` now supports
`--min-positive-instances`; the formal train/dev manifest command should keep
`--min-positive-instances 8` so sparse partial manifests cannot be mistaken for
training-ready artifacts. Smoke/debug manifests can omit the guard only when
they will not be trained or gated.

The formal train/dev manifest command should also use `--require-raw-complete`.
This prevents training from the first few positive instances in a partial
mining snapshot. Reaching `positive_instances >= 8` is a readiness signal; the
formal train manifest should still be built from a complete residual-train raw
snapshot unless the protocol is explicitly changed and documented.

`--require-raw-complete` now also verifies the sample grid: raw sources must
exactly cover the split, all instances must share the same mining sample-seed
set, and every instance/seed must contain `sample_id=0..num_samples_generated-1`
with no duplicates. The audit script checks the same condition on existing
manifests.

Formal elite manifest build/audit now also locks the declared sampling budget:
`finalize_residual_elite_manifest.py` passes its `--sample-seeds` and
`--num-samples` values into `build_residual_elite_replay_manifest.py` and
`audit_residual_elite_replay_manifest.py`. The builder/audit reject raw
artifacts whose `sample_seed` set or `num_samples_generated` differs from that
declared protocol.
Future `run_march_sample_portfolio_multiseed.py` raw artifacts also record
`source_checkpoint` and `source_checkpoint_sha256`. Formal manifest build/audit
validate this raw checkpoint hash when present, while remaining compatible with
older raw artifacts from the already-running residual-train mining job that did
not record these fields.
The sampled portfolio summaries now propagate the recorded checkpoint hash into
`instance_oracle_summary.csv` and related summaries. `decide_residual_portfolio_gate.py`
checks that oracle-summary hash against `--checkpoint` when present, so a
checkpoint gate cannot silently pair an oracle CSV with a different checkpoint.

`train_residual_elite_replay.py` also supports
`--min-train-positive-instances` and `--min-dev-positive-instances`. Formal
replay training should set these guards as a second protection against
bypassing the manifest-builder floor. It now also enforces expected train/dev
split names and `source_checkpoint_sha256`, so residual-heldout artifacts or
elites mined by a different checkpoint cannot be silently trained. The formal
training entry point also checks expected train/dev sample seed sets and
`num_samples_generated`, matching the manifest finalizer protocol. Row-limited
manifest training is rejected by default; `--allow-partial-manifest-training`
is reserved for smoke/debug runs and such checkpoints must not be gated.

Replay training `config.yaml` now records source checkpoint SHA256, train/dev
manifest SHA256, elite row counts, positive-instance counts, expected train/dev
splits, expected train/dev sampling budgets, row-limit settings, and the
train/dev positive floors used by the entry point, so a gated checkpoint can be
audited back to its exact formal replay inputs.
`audit_residual_elite_replay_manifest.py` now has optional replay training
config checks for those hashes/counts/splits/row-limits/floors; run this
before all-49 gating a replay checkpoint.
`decide_residual_portfolio_gate.py` also supports `--training-config-audit` for
replay checkpoints. When supplied, the gate decision refuses audit CSVs that
are missing required formal replay-provenance checks or have any failed check,
and records the audit path/SHA256 in the decision document, so an all-49 replay
checkpoint gate remains tied to the formal train/dev manifest provenance.
It can also write a structured `--record-json` gate artifact. The final
residual portfolio protocol audit can require this record with
`--gate-record ... --require-gate-pass`, and then checks that the gate decision
is `pass`, the gate denominator is non-diagnostic, the referenced oracle
artifact/hash and oracle solved count match the record, the referenced replay
training-config audit artifact/hash has all formal checks with zero failures,
and the held-out selector spec checkpoint hash matches the checkpoint that
passed the all-49 gate.
`run_march_expanded_early_trace_gate.py` now records `checkpoint_sha256` in
`selector_spec.json` for this audit binding.
`finalize_residual_elite_replay_pipeline.py` is now staged. The default
`--stage train_audit` requires train/dev manifest audits to pass and contain
the required formal manifest checks, runs `train_residual_elite_replay.py`, and
audits the saved replay config. Then run the all-49 oracle solver job
separately on `model-dir/best.pt`. Finally, `--stage gate` consumes that oracle
summary and invokes `decide_residual_portfolio_gate.py` with
`--training-config-audit`, after requiring the formal replay training-config
audit checks. The gate stage fails closed if the oracle summary, gate output,
gate name, replay `best.pt`, or training-config audit is missing.

`audit_residual_elite_replay_manifest.py` audits formal train/dev manifests
before replay training. It checks split membership, positive-instance floor,
checkpoint hash, raw CSV hash, CNF path existence, `sample_id` range, and that
manifest rows match solved raw samples. Run it after each guarded manifest is
created and before `train_residual_elite_replay.py`.
`launch_residual_dev_elite_mining.py` is the guarded entry point for starting
residual-dev mining. It refuses to launch unless the train mining progress is
already `ready_for_formal_elite_manifest`, the formal train manifest audit
exists, contains the required formal train manifest checks, all checks pass,
and no March/replay/residual-training processes are visible. Use it instead of
manually starting the dev
`run_march_sample_portfolio_multiseed.py` command.
`finalize_residual_train_when_ready.py` is the guarded train finalization
helper. It refuses to run while the residual-train mining process or March
workers are visible in the local process table, then refreshes progress with
`summarize_residual_elite_mining.py`. It refuses to enter ready/finalizer mode
unless the refreshed progress CSV records `ready_for_formal_elite_manifest`.
The process check is best-effort under sandboxing; the refreshed progress gate
is the hard pre-check before it invokes `finalize_residual_elite_manifest.py`.
After readiness, it also requires per-instance and global mining artifacts to
remain unchanged for a short settle window, which avoids racing a host-side
runner that is still writing final summaries.
The finalizer itself refreshes progress again, requires
`ready_for_formal_elite_manifest`, then runs strict summarize-only,
`--require-raw-complete` manifest build, and audit.

Do not train elite replay yet. After residual-train mining completes and the
positive floor is met, summarize and build the train elite manifest. Run the
final summarize command strictly, without `--allow-partial-summary`; a missing
per-instance raw artifact should fail the command and trigger a resume, not
produce a formal partial aggregate:

```bash
/home/sunshixin/anaconda3/envs/rlaf/bin/python run_march_sample_portfolio_multiseed.py \
  --scope expanded \
  --input runs/analysis/benchmark_transition_band_residual_large/residual_split_seed1729/residual_train.csv \
  --source-root data/benchmark_transition_band_residual_large \
  --checkpoint runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt \
  --out-dir runs/analysis/benchmark_march_residual_train_elite_mining_coverage_diverse_best_iter2 \
  --subset-root data/benchmark_march_residual_train_elite_mining_coverage_diverse_best_iter2 \
  --doc docs/benchmark_march_residual_train_elite_mining_coverage_diverse_best_iter2.md \
  --sample-seeds 1729 \
  --num-samples 16 \
  --artifact-mode instance \
  --full-cpu-lim 60 \
  --workers 8 \
  --device cpu \
  --summarize-only

env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python \
  build_residual_elite_replay_manifest.py \
  --raw-samples runs/analysis/benchmark_march_residual_train_elite_mining_coverage_diverse_best_iter2/raw_samples_all.csv \
  --split-csv runs/analysis/benchmark_transition_band_residual_large/residual_split_seed1729/residual_train.csv \
  --checkpoint runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt \
  --output-csv runs/analysis/benchmark_transition_band_residual_large/residual_train_elite_replay_manifest_coverage_diverse_best_iter2.csv \
  --doc docs/residual_train_elite_replay_manifest_coverage_diverse_best_iter2.md \
  --max-per-instance 4 \
  --min-positive-instances 8 \
  --require-raw-complete \
  --expected-sample-seeds 1729 \
  --expected-num-samples 16

env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python \
  train_residual_elite_replay.py \
  --checkpoint runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt \
  --train-manifest runs/analysis/benchmark_transition_band_residual_large/residual_train_elite_replay_manifest_coverage_diverse_best_iter2.csv \
  --dev-manifest runs/analysis/benchmark_transition_band_residual_large/residual_dev_elite_replay_manifest_coverage_diverse_best_iter2.csv \
  --model-dir runs/GNN_March_3SAT_ResidualEliteReplayCoverageDiverseBestIter2 \
  --epochs 8 \
  --batch-size 8 \
  --lr 5e-6 \
  --kl-penalty 0.05 \
  --min-train-positive-instances 8 \
  --min-dev-positive-instances 4 \
  --expected-train-split residual_train \
  --expected-dev-split residual_dev \
  --expected-train-sample-seeds 1729 \
  --expected-dev-sample-seeds 1729 \
  --expected-train-num-samples 16 \
  --expected-dev-num-samples 16
```

If residual-train also has almost no positives, do not train replay from the
all-49 positives. Continue model-side work toward a stronger objective or
larger train mining seed budget. If train positives are sufficient, repeat the
same mining procedure on residual-dev only for checkpoint selection, never on
heldout.

Residual-dev must use its own mining namespace
`runs/analysis/benchmark_march_residual_dev_elite_mining_coverage_diverse_best_iter2`
and formal manifest
`runs/analysis/benchmark_transition_band_residual_large/residual_dev_elite_replay_manifest_coverage_diverse_best_iter2.csv`.
Run strict summarize-only, build with `--min-positive-instances 4` and
`--require-raw-complete`, then audit before starting
`train_residual_elite_replay.py`.

`finalize_residual_elite_manifest.py` now wraps the train/dev formal manifest
finalization sequence: progress readiness gate, strict summarize-only,
`--require-raw-complete` manifest build, expected sampling-budget checks,
audit, and audit-pass enforcement. Use it instead of manually running partial
command sequences when mining completes.
The progress readiness gate now requires `positive_floor_met=true`,
`complete_mining=true`, and `raw_artifacts_complete=true`; it also parses CSV
boolean cells strictly, so string `False` cannot pass as truthy. The mining
progress summary counts only split members with audited complete raw grids and
reports unexpected artifacts from other split/namespace directories.

新增进度汇总脚本：

```text
summarize_residual_elite_mining.py
tests/test_residual_elite_mining_summary.py
```

用途：只读 per-instance summary，不启动 solver，输出 completed/remaining/
positive_instances/solved_samples 和 protocol decision。

当前验证：

```bash
env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python -m unittest \
  tests.test_residual_elite_replay \
  tests.test_residual_elite_mining_summary \
  tests.test_residual_training_objective \
  tests.test_residual_portfolio_protocol
```

结果：`17 tests OK`。

2026-06-02 additional guard validation:

```bash
env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python -m unittest \
  tests.test_finalize_residual_elite_manifest \
  tests.test_residual_elite_mining_summary \
  tests.test_residual_elite_replay \
  tests.test_residual_elite_manifest_audit \
  tests.test_march_sample_portfolio_summarize
```

Result: `31 tests OK`.

## 2026-06-03 residual portfolio status update

The first contrastive replay checkpoint was a valid diagnostic run but failed
the unchanged all-49 oracle gate:

```text
runs/GNN_March_3SAT_ResidualContrastiveReplayCoverageDiverseBestIter2/best.pt
sha256: 56dba0670da653bea7a8106c5db2ca34463928bd8f13c5bb302dd47da313562c
gate: residual_contrastive_replay_coverage_diverse_best_iter2_all49
oracle_solved: 2/49
positives:
  - 410/3sat_12.cnf
  - 425/3sat_28.cnf
size-440 positives: 0/30
decision: fail
```

The original contrastive objective had a real bug: shuffled batches created
arbitrary positive/negative pairings instead of same-CNF contrastive groups.
`train_residual_contrastive_replay.py` has been fixed to preserve
`contrastive_group_id`, batch by groups, and use group-aware pairwise margin
loss on `delta_log_prob_per_var` relative to the source checkpoint by default.
The related tests pass:

```text
env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python -m unittest \
  tests.test_residual_oracle_union \
  tests.test_residual_contrastive_replay \
  tests.test_residual_elite_replay \
  tests.test_residual_training_objective

34 tests OK
```

A group-aware contrastive checkpoint was then trained but should not be sent to
the all-49 March gate under the current protocol:

```text
model_dir: runs/GNN_March_3SAT_ResidualContrastiveGroupAwareCoverageDiverseBestIter2
best.pt sha256: c3fec51c29de5097a6d157dfe6d4385ecae349d07bccfedf341e85d144c44a04
last.pt sha256: 2d6ba175929369fa3582cd47042bfd38f04442368817f0014150ef38884aceb3
best epoch: 7
best dev score: -0.701538602511088
```

Reason: train separation improves, but dev separation does not. In
`metrics.csv`, dev pairwise worsens from about `0.70318` to `0.70420`, and the
positive delta score remains lower than the negative delta score at the end.
This is not enough evidence to spend another all-49 solver gate. Treat this as
a model-side diagnostic, not a gate candidate, unless the user explicitly asks
for a diagnostic run.

An oracle-union diagnostic across the six completed all-49 checkpoint gates is
now available:

```text
doc: docs/residual_all49_oracle_union_current_checkpoints.md
csv: runs/analysis/benchmark_transition_band_residual_large/residual_all49_oracle_union_current_checkpoints.csv
checkpoint diagnostics: 6
residual instances: 49
union oracle solved: 2/49
union positives:
  - 410/3sat_12.cnf
  - 425/3sat_28.cnf
size-440 union positives: 0/30
```

This changes the active decision. The current bottleneck is not selector
quality and not checkpoint ensembling; it is sparse model/sampling coverage in
the residual distribution. Therefore:

```text
Do not tune top-k, dead_ends thresholds, adaptive selector rules, or learned
selectors.
Do not touch held-out.
Do not run same-budget non-neural control yet.
Do not rerun failed objectives as-is.
Do not gate the group-aware contrastive checkpoint unless explicitly requested
as a diagnostic.
```

The next viable branch is residual train/dev mining expansion in fresh
namespaces. Reuse the existing single-seed `1729` mining artifacts as one raw
source, mine additional sample seeds separately, and only then rebuild
elite/contrastive manifests with strict expected seed checks:

```text
source checkpoint:
  runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt

existing raw seed:
  1729

new mining seeds:
  1730,1731,1732

new train namespace:
  runs/analysis/benchmark_march_residual_train_multiseed_mining_coverage_diverse_best_iter2
  data/benchmark_march_residual_train_multiseed_mining_coverage_diverse_best_iter2

new dev namespace:
  runs/analysis/benchmark_march_residual_dev_multiseed_mining_coverage_diverse_best_iter2
  data/benchmark_march_residual_dev_multiseed_mining_coverage_diverse_best_iter2
```

After train/dev mining completes, build new manifests from both old and new raw
CSV files and require:

```text
expected sample seeds: 1729,1730,1731,1732
expected num samples: 16
require raw complete: true
```

Only train a new coverage-oriented residual checkpoint if the expanded mining
meaningfully raises positive-instance coverage and size-440 diversity. If
expanded mining remains sparse, abandon this policy/objective family and move
to a stronger model-side change rather than selector work. Any new checkpoint
must return to the unchanged all-49 oracle gate, and selector/protocol freeze
only resumes after `oracle_solved >= 5/49`.

## 2026-06-05 residual multiseed mining progress

The residual-train mining expansion for new sample seeds has been launched
outside the sandbox so it can keep running after Codex exits:

```text
pid: 3140840
checkpoint: runs/GNN_March_3SAT_ResidualCoverageDiverseBestIter2/best.pt
split: runs/analysis/benchmark_transition_band_residual_large/residual_split_seed1729/residual_train.csv
sample seeds: 1730,1731,1732
num samples per seed: 16
out_dir: runs/analysis/benchmark_march_residual_train_multiseed_mining_coverage_diverse_best_iter2
subset_root: data/benchmark_march_residual_train_multiseed_mining_coverage_diverse_best_iter2
log: runs/analysis/benchmark_transition_band_residual_large/logs/residual_train_multiseed_mining_coverage_diverse_best_iter2.log
```

Do not start dev mining while this process or its March workers are still
running. Monitor it with:

```bash
pgrep -af 'run_march_sample_portfolio_multiseed.py --scope expanded --input runs/analysis/benchmark_transition_band_residual_large/residual_split_seed1729/residual_train.csv'
pgrep -af 'solvers/march_weighted/march_nh /home/sunshixin/chenchao/my_rlaf/data/tmp/march_'
```

New helper:

```text
summarize_residual_multiseed_mining.py
tests/test_residual_multiseed_mining_summary.py
launch_residual_dev_multiseed_mining.py
tests/test_launch_residual_dev_multiseed_mining.py
finalize_residual_multiseed_mining.py
tests/test_finalize_residual_multiseed_mining.py
```

Why it exists: the old `summarize_residual_elite_mining.py` is instance-level.
The new expansion has a completion grid of `instance x sample_seed`; using the
old summarizer would misread a single completed seed as a completed instance.
The dev launcher exists to prevent accidental residual-dev mining before train
multi-seed mining has completed and met the positive floor.
The multiseed finalizer exists to prevent writing global
`raw_samples_all.csv` from partial per-instance artifacts. It refreshes
multi-seed progress and then runs strict `--summarize-only` only after the
train grid is complete. It also checks the runner's
`.run_march_sample_portfolio_multiseed.lock`; this is more reliable than
host-process discovery from inside the sandbox.

Current train progress artifact:

```text
doc: docs/residual_train_multiseed_mining_progress_coverage_diverse_best_iter2.md
csv: runs/analysis/benchmark_transition_band_residual_large/residual_train_multiseed_mining_progress_coverage_diverse_best_iter2.csv
remaining:
  runs/analysis/benchmark_transition_band_residual_large/residual_train_multiseed_mining_remaining_coverage_diverse_best_iter2.csv
positives:
  runs/analysis/benchmark_transition_band_residual_large/residual_train_multiseed_mining_positives_coverage_diverse_best_iter2.csv
```

Latest observed progress:

```text
expected_instances: 168
expected_seed_pairs: 504
completed_seed_pairs: 10
completed_instances_all_seeds: 3
positive_instances: 0
positive_seed_pairs: 0
solved_samples: 0
decision: continue_mining
```

The relevant tests pass:

```text
env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python -m unittest \
  tests.test_finalize_residual_multiseed_mining \
  tests.test_launch_residual_dev_multiseed_mining \
  tests.test_residual_multiseed_mining_summary

22 tests OK

env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python -m unittest \
  tests.test_residual_multiseed_mining_summary \
  tests.test_residual_elite_mining_summary \
  tests.test_residual_elite_replay

30 tests OK
```

Current guard validation:

```text
env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python \
  launch_residual_dev_multiseed_mining.py --dry-run

expected result while train progress is partial:
  ValueError: Train multiseed mining progress is not ready for residual-dev launch

env PYTHONPATH=. /home/sunshixin/anaconda3/envs/rlaf/bin/python \
  finalize_residual_multiseed_mining.py --dry-run

expected result while train runner is active:
  status=wait active_work_dir_lock
```

Next decision rule:

```text
1. Let train multiseed mining finish or resume it until
   completed_seed_pairs=504 and raw_artifacts_complete=true.
2. If train positives/diversity are still weak, do not start dev mining or
   train another replay checkpoint; switch to a stronger model-side objective.
3. If train mining has enough positives, run dev multiseed mining in its fresh
   namespace, then strict summarize-only for train/dev, then build expanded
   manifests from old 1729 raw plus new 1730/1731/1732 raw.
4. Only after a new checkpoint passes all-49 oracle `>=5/49` may selector,
   held-out, and same-budget non-neural control resume.
```
