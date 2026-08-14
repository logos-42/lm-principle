# lm_principle（中文文档）

> 用 **Lean 4 + mathlib** 把"大模型的数学第一性原理"写成可机器验证的定理，
> 而不是论文里的启发式论证。

本仓库把现代神经网络架构（RNN、CNN、Transformer）背后的核心数学结论
形式化为可验证的证明。旗舰案例是 **LMT-twister**（反事实表示瓶颈）与
**分形必要性**——涵盖容量计数、IE / EHS 结构，以及一条完整、有定理背书的
论证：为何分形组织、残差回馈与最优深度从第一性原理涌现。

**83 条定理已机器验证**（`lake build` 全绿，无 `sorry` / `admit` / `axiom`），
并由 **pre-push 门禁** 守护（验证通过才允许推送）。

英文主文档：[README.md](./README.md)

---

## 为什么做这个

神经架构通常用直觉或经验曲线来论证。本项目要求更严格的标准：一个结论
只有当 `lake build` 全绿、且证明中**不含 `sorry` / `admit` / `axiom`** 时才被接受。

四条架构第一性原理（形式化于 `LmPrinciple/`）：

1. **RNN = 因果卷积**：线性递归展开后 `h(n+1) = Σ w^(n-k) x(k)`，与 CNN 共享群代数结构。
2. **CNN = 群代数乘法**：平移等变性就是乘法的结合律，不需要分析。
3. **Transformer 注意力 = 凸组合**：`softmax` 归一 ⟹ 输出在凸包内；置换等变 ⟹ 位置信息必须外部注入。
4. **容量 = 计数**：`R` 比特最多 `2^R` 个状态，区分 `V` 个动作需 `≥ log₂V` 比特——LMT-twister 主定理 2.1 的离散骨架。

在此基础上，**分形必要性** 主线把一组直觉断言（分形省参数、高维表示不坍缩、
最优深度有限、默里定律 `0.79` 被物理锁定）从"断言"升级为无条件、无经验数据依赖的机器证明。

---

## 已验证结论（每条都有 Lean 定理背书）

> 分形必要性 → 83 条机器验证定理。以下每条均由 Lean 定理背书。

1. **分形组织比均匀堆叠更快**（核心假设 ✓）
   — `prefix_allocation_optimal` / `fractal_beats_uniform`：只要每层自由能下降量 `Δ_k` 严格递减，预算集中前缀（分形稀疏）的总收益 `≥` 均匀平摊——"分形省 25% 参数"不是巧合，是定理。

2. **高维结构不坍缩**（假设 ✓）
   — `residual_no_collapse_n`：收缩残差 `⟹` n 层后输出距离 `≥ (1-c)^n·` 输入距离（确定性下界，坍缩概率 `= 0`）。回馈是**充分**保证：`ffn_can_collapse` 给出无回馈 FFN 存在坍缩到常数的实现（无回馈不保证不坍缩，但允许坍缩）。

3. **信息流动效率**（假设 ✓）
   — RNN 乘性记忆 `≤ |w|^t` 指数消失，LSTM 门控记忆 `≥ α^t` 指数保留（`α` 可学到 1）：门控结构参数效率更高；注意力每参数交互率 `n²/(3d²)` 在 `3d² < n` 时反超 RNN——长序列的规模经济。

4. **自由能最小化依赖特定信息结构**（假设 ✓）
   — Gibbs 不等式 `KL ≥ 0`（变分自由能非负）+ 交叉熵 `= 熵 + KL ≥ 熵`；`hypothesis_verification` 组装全部结构定理：依赖的信息结构 = ① 恒等 / 门控回馈（防坍缩 + 保留）② 凸组合（误差有界）③ 前缀参数集中（分形分配）④ 交叉熵下界。

5. **默里定律 `0.79` 完整推导**（C1 ✓）
   — `murray_variational_optimal`：两项成本 `C(r)=a/r⁴+b·r²` 在 `r⁶=2a/b` 处全局最小（纯代数证明，免微积分）。实验一悖论是**带精确机制的模型错配**：原成本和的阻力项漏了流量守恒因子（`Q_g = Q/2^g`）；补上后全局最优变为内点并收敛到 `2^(-1/3)`（`diagnose_murray_cost.py`：`G=50` 得 `0.795`，差 0.13%）。流量守恒 `⟹ r³=r₁³+r₂³` + 对称 `⟹ ρ³=1/2` 完整链闭合。诚实边界：纯输送成本下分叉比不分叉贵 `2^(1/3)` 倍——分叉的存在理由是**覆盖**（空间填充），默里定律给出"必须分叉时的最优比率"。

6. **最优深度在什么条件成立**（C2 + C4 ✓）
   — 条件 = ① 收益严格递减 ② 成本 > 0 ③ 收益最终低于成本 `⟹` 最优深度存在且 `≤ k₀+1`；若 ③ 不成立则"越深越好"——"深度不是越深越好"的精确充要条件。**临界点定理**（`CriticalPoint.lean`，`optimal_depth_is_first_crossing`）：在 ①–③ 下最优深度恰为 `k* = min{k : Δ_k < λ}`——边际收益第一个跌破成本的层；幂律收益 `Δ_k = c/(k+1)²` 时闭式解 `k* = ⌈√(c/λ)⌉ - 1`（`power_law_critical_pair`，数值验证见 `verify_critical_point.py`）。

---

## 已形式化内容

全部位于 `LmPrinciple/`，经 `lake build` 验证（合计 83 条定理）：

| 模块 | 内容 |
|---|---|
| `RNN.lean` | 线性 RNN 闭式解 = 因果卷积（任意 `CommSemiring`）；稳定性 `|w|<1 ⟹` 状态有界（2） |
| `CNN.lean` | 卷积 = 群代数乘法；平移等变性 = 结合律（4） |
| `Transformer.lean` | `softmax` 凸组合；自注意力置换等变（3） |
| `LMT.lean` | 容量计数（鸽巢）；复 SSM = RNN 复化；IE / EHS 结构（7） |
| `Fractal.lean` | 分形必要性：`prefix_allocation_optimal`、`fractal_beats_uniform`、连接密度幂律 + 凸性（9） |
| `ArchCompare.lean` | `residual_no_collapse_n`、`ffn_can_collapse`、LSTM 保留 vs RNN 衰减（5） |
| `Efficiency.lean` | 每参数交互率、注意力反超 `3d²<n`、遗忘门保留（8） |
| `InfoDynamics.lean` | Gibbs `KL≥0`、CE = H + KL、质量流、防坍缩保证、回馈系数、`hypothesis_verification`（12） |
| `Murray.lean` | 变分最优 `r⁶=2a/b`、流量守恒、对称比率 `ρ³=1/2`、最优深度存在、幂律实例化（10） |
| `Training.lean` | 缩放律、CE ≥ 熵、RLHF softmax、DPO 损失 ≥ 0、稀疏 MoE/注意力保界（10） |
| `CriticalPoint.lean` | `optimal_depth_is_first_crossing`（`k* = min{k : Δ_k < λ}`）、幂律临界点对（3） |
| `Hopfield.lean` | 能量差分 `E(s')-E(s)=(s_i-s'_i)·net_i`、翻转严格下降、现代 Hopfield = 凸组合 = 注意力、softmax 集中性 + 检索锁定误差界 `\|x_new-X_i\| ≤ n·e^{-βΔ}·M`（6） |
| `Maxwell.lean` | 1D 格点麦克斯韦：交叉项 telescoping、能量守恒（无质量）、质量项衰减 `dH/dt = -m²ΣE²`——预言 `τ_G = 1/(6M₀²)`（m_G = √3·M₀ 假设下）（4） |

> 截至 2026-08-13：`lake build` 全绿，**83 条定理**全部机器验证
> （mathlib 闭包从固定 pin 源码编译）；pre-push 门禁生效。

---

## 价值

- **断言 → 定理**：C1–C4 从"断言"升级为无条件、无经验数据依赖的机器证明。实验提供数值证据，定理提供保证，两者互证。
- **最诚实的一环**：实验一的悖论没有掩盖，其机制被**精确定位**——阻力项漏流量守恒因子（`diagnose_murray_cost.py`；补上后内点最优收敛 `2^(-1/3)`）。"承认边界 + 用更完整的数学闭合"是科学写作的最优形态。
- **本地真实实验 + 诚实修正**：三个实验本地复现（PyTorch CPU、seed 42、与原文差 < 0.01）；多 seed 复跑（`experiments_v2.py`，3 seeds）暴露了**不成立**的部分：分形 vs 均匀跨 seed 不显著、"4 层起损失断崖"是单次训练假象——而最优深度 2 与临界点 `k* = min{k : Δ_k < λ}` 稳健成立。
- **可复现流水线**：wiki-first 编译 + 83 条定理全验证 + pre-push 门禁（验证无错误才能推送）——整个论证链可复现、可继承、可扩展。

---

## 仓库结构

```
lm_principle/
├── LmPrinciple/          # Lean 4 形式化（已验证层）
│   ├── Basic.lean
│   ├── RNN.lean
│   ├── CNN.lean
│   ├── Transformer.lean
│   ├── LMT.lean
│   └── Fractal.lean
├── docs/wiki/            # Wiki 知识系统（LLM Wiki v2 schema）
├── scripts/              # Wiki 校验脚本 + 环境搭建 + pre-push 门禁
├── manifests/            # 原始资料登记（raw_sources.csv）
├── lakefile.toml         # 本地（离线）mathlib 物化
├── lean-toolchain        # leanprover/lean4:v4.21.0
├── README.md
└── README.zh.md
```

知识分层为 **raw → wiki → code**：

- **raw**：原始资料（登记在 `manifests/raw_sources.csv`）
- **wiki**：编译后的当前共识（`docs/wiki/`，v2 schema）
- **code**：执行层（`LmPrinciple/`）

---

## 构建

环境要求：

- [elan](https://github.com/leanprover/elan) + Lean **4.21.0**
- mathlib **v4.21.0**（rev `308445d`，2025-06-30）

mathlib 及其 8 个依赖通过本地 `path` require（`lakefile.toml`）固定，构建时无需联网：

```bash
lake build              # 真实 lake 二进制；Windows 见 scripts/run_build.sh
lake build LmPrinciple  # 只构建形式化部分
```

全新环境搭建见 `scripts/setup_mathlib.sh`（Windows 专用）与
`docs/wiki/current-status.md` 的"环境搭建流程"。

> ⚠️ 不要把 `lean-toolchain` 改回 `v4.34.0-rc1`——Batteries 语法不兼容，会编译失败。

---

## Wiki 系统（wiki-first）与 pre-push 门禁

结论需写回 `docs/wiki/`，使用 **LLM Wiki v2 schema**（见 `docs/wiki/SCHEMA.md`）。
校验与编译脚本在 `scripts/`：

```bash
python3 scripts/wiki_lint.py --strict=v2   # schema 校验
python3 scripts/wiki_check.py              # 完整性检查
python3 scripts/delta_compile.py --write-drafts
```

非代码文件（PDF、Excel、图片、压缩包等）使用前必须登记：

```bash
python3 scripts/ingest_raw.py              # 登记新 raw
python3 scripts/untracked_raw_check.py     # 查找漏登 raw
```

**pre-push 门禁** 确保 `lake build` 全绿（无 `sorry` / `admit` / `axiom`）才允许推送——
验证是硬前置条件，不是建议。

---

## 状态与路线图

**已完成**

- ✅ Lean 4.21.0 + mathlib v4.21.0 环境，全离线物化
- ✅ **83 条定理**机器验证，覆盖 RNN / CNN / Transformer / LMT / Fractal
- ✅ 分形必要性论证：C1（默里 `0.79`）与 C2+C4（最优深度）已证
- ✅ Wiki-first 知识系统（v2 bootstrap，lint 全绿）+ pre-push 门禁生效

**待办（可选项）**

- ① 导数版变分验证（`deriv` 驻点）——待 `Mathlib.Analysis.Calculus`；代数版已闭合论证
- ② `D → n*` 闭式解（分形维数 → 最优深度）——**收益临界点已闭式**（`k* = ⌈√(c/λ)⌉ - 1`），但任务分形维数 `D` 到逐层收益 `Δ_k` 的映射仍开放
- ③ LMT-twister 主定理 2.1 信息论证明（引理 A.1–A.4：IE 容量经 DPI → Fano → EHS）。
  mathlib 武器已确认就位：`Mathlib/InformationTheory/Hamming.lean`（Fano）与
  `Mathlib/InformationTheory/KullbackLeibler/`（互信息 + DPI）

**诚实标注的边界**

- 交叉熵 / 熵定义在有限离散分布（`Fin n`）上——连续版本需测度论
- `D → n*` 闭式解（分形维数到深度）仍开放；收益临界点闭式已验证
- 多 seed 实验显示分形 vs 均匀**性能差异不显著**（3 seeds）；被验证的主张是
  参数效率（同性能少 25% 参数），不是损失更低

---

## 来源

- 论文稿（IEEE 期刊 + 会议版）：`paper/main_jrnl.tex`、`paper/main_conf.tex`——《LLM动力学下的数学分形临界》（英文标题 *Mathematical Fractal Criticality in LLM Dynamics*）
- LMT-twister 论文 `head-en.tex` / `head-zh.tex`（附录 A，引理 A.1–A.4）
- 分形必要性论证：`LmPrinciple.Fractal` + `docs/wiki/fractal-necessity.md`
- 架构概览：`docs/wiki/project-overview.md`
- 实时状态：`docs/wiki/current-status.md`
- 本地实验：`experiments/run_fractal_experiments.py` + `scripts/experiments_v2.py`（多 seed 诚实复跑）+ `scripts/diagnose_murray_cost.py`（悖论诊断）

远程仓库：`git@github.com:logos-42/lm-principle.git`

## 开源许可

本项目采用 **MIT License**——见 [LICENSE](./LICENSE)。形式化代码（`LmPrinciple/`）为机器验证的 Lean 4 代码；论文稿与 wiki 内容为作者原创。Lean 4、mathlib 与 PyTorch 各归其各自许可。
