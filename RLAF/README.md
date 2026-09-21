# EchoSAT

EchoSAT 是在 RLAF 基础上扩展的 SAT 神经引导求解项目。当前主线是：

- 慢模型：GNN 生成静态变量权重和极性先验。
- 快反馈：Glucose rollout 收集变量级 solver event state。
- 快模型：trace-pretrained gated residual adapter 只做低频残差修正。
- 风险控制候选：ultra-conservative counterfactual risk selector 决定是否启用 adapter，优先避免丢失 base-solved 实例。

当前 selector 不是为了“尽可能多开 adapter”，而是先把翻车风险压住。它在 small trace repeated split 上表现安全，但 disjoint 300/350 评估没有复现稳定收益，因此暂不能作为最终主结果。

## 环境配置

推荐使用 `conda`：

```bash
conda create -n rlaf python=3.12
conda activate rlaf
```

安装依赖：

```bash
pip install -e .
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.5.0+cu124.html
```

如果不是 CUDA 12.4，请把 `cu124` 替换为本机 CUDA 版本；CPU 环境使用对应的 `cpu` wheel。

编译 SAT solver：

```bash
bash build_solvers.sh
```

下载 RLAF 数据后放到项目目录并解压：

```bash
unzip data.zip
```

## RLAF 基线训练

训练 Glucose 版本：

```bash
python train_rlaf.py model_name=GNN_Glucose_3SAT solver.solver=glucose dataset.train_path=data/training/3sat/*/*.cnf dataset.val_path=data/validation/3sat/*/*.cnf optim.lr=0.0001 training.kl_penalty=0.1
python train_rlaf.py model_name=GNN_Glucose_Coloring solver.solver=glucose dataset.train_path=data/training/coloring/*/*.cnf dataset.val_path=data/validation/coloring/*/*.cnf optim.lr=0.00005 training.kl_penalty=1.1
python train_rlaf.py model_name=GNN_Glucose_Crypto solver.solver=glucose dataset.train_path=data/training/crypto/*.cnf dataset.val_path=data/validation/crypto/*.cnf optim.lr=0.00005 training.kl_penalty=0.1
```

训练 March 版本：

```bash
python train_rlaf.py model_name=GNN_March_3SAT solver.solver=march dataset.train_path=data/training/3sat/*/*.cnf dataset.val_path=data/validation/3sat/*/*.cnf optim.lr=0.0001 training.kl_penalty=1.0
python train_rlaf.py model_name=GNN_March_Coloring solver.solver=march dataset.train_path=data/training/coloring/*/*.cnf dataset.val_path=data/validation/coloring/*/*.cnf optim.lr=0.00001 training.kl_penalty=0.1
python train_rlaf.py model_name=GNN_March_Crypto solver.solver=march dataset.train_path=data/training/crypto/*.cnf dataset.val_path=data/validation/crypto/*.cnf optim.lr=0.00001 training.kl_penalty=0.1
```

监督模型训练：

```bash
python train_supervised.py model_name=GNN_Backbone_3SAT target=backbone dataset.train_path=data/training/3sat/sat/*.cnf dataset.val_path=data/validation/3sat/sat/*.cnf
python train_supervised.py model_name=GNN_Core_Coloring target=core dataset.train_path=data/training/coloring/*/*.cnf dataset.val_path=data/validation/coloring/unsat/*.cnf
python train_supervised.py model_name=GNN_Core_Crypto target=core dataset.train_path=data/training/crypto/*.cnf dataset.val_path=data/validation/crypto/*.cnf
```

## Trace Distillation

EchoSAT 加入了 event trace distillation，用来预训练 slow-fast adapter。当前 weighted Glucose 可以输出这些变量级事件字段：

- `event_var_low_lbd_learnt_lits`
- `event_var_useful_decisions`
- `event_var_conflict_lits`
- `event_var_propagations`
- `event_var_activity`

生成 adapter 预训练数据：

```bash
python generate_trace_distillation_data.py --config-name config_generate_trace_distillation \
  from_checkpoint='runs/GNN_Glucose_3SAT_V1/best.pt' \
  dataset.path='data/training/3sat/*/*.cnf' \
  trace.output_path='data/trace_distill/train_trace.pt'
```

只训练 event adapter：

```bash
python train_trace_distill.py --config-name config_train_trace_distill \
  from_checkpoint='runs/GNN_Glucose_3SAT_V1/best.pt' \
  trace.data_path='data/trace_distill/train_trace.pt'
```

伪标签会提升低 LBD learnt involvement、useful decision、conflict involvement、propagation count 和 activity 排名靠前的变量。默认损失只监督权重/log-scale 残差，并保留慢 GNN 的极性先验。

## Counterfactual Risk Selector

当前 EchoSAT 的 risk-controller 候选是 ultra-conservative counterfactual risk controller。它的目标不是扩大 adapter 使用率，而是在一次 conflict-budgeted solver rollout 后，只允许低风险的 slow-fast intervention。

主线 checkpoint：

```text
runs/GNN_Glucose_3SAT_CounterfactualRiskSelectorSmall300350_UltraConservative/best.pt
```

评估 300/350/400：

```bash
python evaluate_guided_solver.py --config-name config_eval_guided_solver_counterfactual_risk_selector \
  dataset.eval_path='data/test/3sat/300/*.cnf' \
  save_file=eval_counterfactual_risk_selector_300.csv

python evaluate_guided_solver.py --config-name config_eval_guided_solver_counterfactual_risk_selector \
  dataset.eval_path='data/test/3sat/350/*.cnf' \
  save_file=eval_counterfactual_risk_selector_350.csv

python evaluate_guided_solver.py --config-name config_eval_guided_solver_counterfactual_risk_selector \
  dataset.eval_path='data/test/3sat/400/*.cnf' \
  save_file=eval_counterfactual_risk_selector_400.csv
```

相关文档：

- `docs/current_mainline_counterfactual_risk_selector.md`
- `docs/counterfactual_risk_selector_disjoint_300350.md`
- `docs/counterfactual_outcome_trace_generation.md`
- `docs/counterfactual_risk_selector_training_results.md`

## Fixed Rho Gate 基线

Fixed base-rho gate 是 trace-pretrained gated residual adapter 的受控基线：

```bash
python evaluate_guided_solver.py --config-name config_eval_guided_solver_rho_gate \
  dataset.eval_path='data/test/3sat/350/*.cnf' \
  save_file=eval_trace_adapter_350_round1_conf500.csv
```

完整 300/350/400 消融记录在：

```text
docs/fixed_rho_gate_ablation_results.md
```

## Literal Polarity SBE Adapter

项目也保留 literal-level polarity event state 与 SBE gated-fusion adapter 的实验分支：

```bash
python generate_trace_distillation_data.py --config-name config_generate_trace_distillation_polarity
python train_trace_distill.py --config-name config_train_trace_distill_sbe_polarity
python evaluate_guided_solver.py --config-name config_eval_guided_solver_sbe_polarity
```

实验结论与负结果分析见：

```text
docs/literal_polarity_sbe_adapter.md
```

## 常规评估

评估 RLAF-guided Glucose：

```bash
python evaluate_guided_solver.py model_name=GNN_Glucose_3SAT dataset.eval_path=data/test/3sat/450/*.cnf
```

评估 supervised 模型：

```bash
python evaluate_guided_solver.py model_name=GNN_Backbone_3SAT dataset.eval_path=data/test/3sat/450/*.cnf is_supervised=True pred_scale=10.0
```

评估原生 solver：

```bash
python evaluate_base_solver.py solver.solver=glucose dataset.eval_path=data/test/3sat/450/*.cnf
```

实例级结果会写入对应 `runs/...` 目录下的 CSV 文件。
