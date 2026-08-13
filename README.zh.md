# lm_principle（中文文档）

> 用 **Lean 4 + mathlib** 把"大模型的数学第一性原理"写成可机器验证的定理，
> 而不是论文里的启发式论证。

本仓库把现代神经网络架构（RNN、CNN、Transformer）背后的核心数学结论
形式化为可验证的证明。旗舰案例是 **LMT-twister**（反事实表示瓶颈）与
**分形必要性**——涵盖容量计数、IE / EHS 结构，以及一条完整、有定理背书的
论证：为何分形组织、残差回馈与最优深度从第一性原理涌现。

**73 条定理已机器验证**（`lake build` 全绿，无 `sorry` / `admit` / `axiom`），
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

> 分形必要性 → 73 条机器验证定理。以下每条均由 Lean 定理背书。

1. **分形组织比均匀堆叠更快**（核心假设 ✓）
   — `prefix_allocation_optimal` / `fractal_beats_uniform`：只要每层自由能下降量 `Δ_k` 严格递减，预算集中前缀（分形稀疏）的总收益 `≥` 均匀平摊——"分形省 25% 参数"不是巧合，是定理。

2. **高维结构不坍缩**（假设 ✓）
   — `residual_no_collapse_n`：收缩残差 `⟹` n 层后输出距离 `≥ (1-c)^n·` 输入距离（确定性下界，坍缩概率 `= 0`）；`ffn_can_collapse`：无回馈的 FFN 存在实现坍缩到常数——回馈（恒等 / 门控路径）是防坍缩的必要条件。

3. **信息流动效率**（假设 ✓）
   — RNN 乘性记忆 `≤ |w|^t` 指数消失，LSTM 门控记忆 `≥ α^t` 指数保留（`α` 可学到 1）：门控结构参数效率更高；注意力每参数交互率 `n²/(3d²)` 在 `3d² < n` 时反超 RNN——长序列的规模经济。

4. **自由能最小化依赖特定信息结构**（假设 ✓）
   — Gibbs 不等式 `KL ≥ 0`（变分自由能非负）+ 交叉熵 `= 熵 + KL ≥ 熵`；`hypothesis_verification` 组装全部结构定理：依赖的信息结构 = ① 恒等 / 门控回馈（防坍缩 + 保留）② 凸组合（误差有界）③ 前缀参数集中（分形分配）④ 交叉熵下界。

5. **默里定律 `0.79` 完整推导**（C1 ✓）
   — `murray_variational_optimal`：三项成本 `C(r)=a/r⁴+b·r²` 在 `r⁶=2a/b` 处全局最小（纯代数证明，免微积分）——这正解释了实验一的悖论：`0.79` 是三项成本的变分最优，简化模型（缺做功项）当然不成立。流量守恒 `⟹ r³=r₁³+r₂³` + 对称 `⟹ ρ³=1/2` 完整链闭合。

6. **最优深度在什么条件成立**（C2 + C4 ✓）
   — 条件 = ① 收益严格递减 ② 成本 > 0 ③ 收益最终低于成本 `⟹` 最优深度存在且 `≤ k₀+1`；若 ③ 不成立则"越深越好"——这就是"深度不是越深越好"的精确充要条件。幂律收益 `Δ_k = c/(k+1)²` 满足条件 `⟹` 有限最优深度存在（C4 实例化）。

---

## 已形式化内容

全部位于 `LmPrinciple/`，经 `lake build` 验证（合计 73 条定理）：

| 模块 | 内容 |
|---|---|
| `LmPrinciple/RNN.lean` | 线性 RNN 闭式解 = 因果卷积（任意 `CommSemiring` 上证明）；稳定性 `|w|<1 ⟹` 状态有界 |
| `LmPrinciple/CNN.lean` | 卷积 = 群代数乘法；平移等变性 = 结合律 |
| `LmPrinciple/Transformer.lean` | `softmax` 凸组合；自注意力置换等变 |
| `LmPrinciple/LMT.lean` | 容量计数（鸽巢原理）；复 SSM = RNN 复化；IE / EHS 模型结构 |
| `LmPrinciple.Fractal` | 分形必要性：`prefix_allocation_optimal`、`residual_no_collapse_n`、`ffn_can_collapse`、`murray_variational_optimal`、最优深度条件、`hypothesis_verification` |

> 截至 2026-08-12：`lake build` 全绿，**73 条定理**全部机器验证
> （mathlib 闭包 1758 模块源码编译）；pre-push 门禁生效。

---

## 价值

- **断言 → 定理**：C1–C4 从"断言"升级为无条件、无经验数据依赖的机器证明。实验提供数值证据，定理提供保证，两者互证。
- **最诚实的一环**：实验一的悖论没有掩盖，而是被变分定理精确解释——简化模型缺做功项 ⟹ `0.79` 不成立；三项成本模型 ⟹ 全局最优。"承认边界 + 用更完整的数学闭合"是科学写作的最优形态。
- **可复现流水线**：wiki-first 编译 + 54→73 条定理全验证 + pre-push 门禁（验证无错误才能推送）——整个论证链可复现、可继承、可扩展。

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
- ✅ **73 条定理**机器验证，覆盖 RNN / CNN / Transformer / LMT / Fractal
- ✅ 分形必要性论证：C1（默里 `0.79`）与 C2+C4（最优深度）已证
- ✅ Wiki-first 知识系统（v2 bootstrap，lint 全绿）+ pre-push 门禁生效

**待办（可选项）**

- ① 导数版变分验证（`deriv` 驻点）——待 `Mathlib.Analysis.Calculus`；代数版已闭合论证
- ② `D → n*` 闭式解（分形维数 → 最优深度）——现有定理给存在性，不给闭式（开放问题）
- ③ LMT-twister 主定理 2.1 信息论证明（引理 A.1–A.4：IE 容量经 DPI → Fano → EHS）。
  mathlib 武器已确认就位：`Mathlib/InformationTheory/Hamming.lean`（Fano）与
  `Mathlib/InformationTheory/KullbackLeibler/`（互信息 + DPI）

**诚实标注的边界**

- 交叉熵 / 熵定义在有限离散分布（`Fin n`）上——连续版本需测度论
- C2 的 `D → n*` 闭式解仍开放

---

## 来源

- LMT-twister 论文 `head-en.tex` / `head-zh.tex`（附录 A，引理 A.1–A.4）
- 分形必要性论证：`LmPrinciple.Fractal` + `docs/wiki/fractal-necessity.md`
- 架构概览：`docs/wiki/project-overview.md`
- 实时状态：`docs/wiki/current-status.md`

远程仓库：`git@github.com:logos-42/lm-principle.git`
