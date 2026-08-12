# lm_principle（中文文档）

> 用 **Lean 4 + mathlib** 把"大模型的数学第一性原理"写成可机器验证的定理，
> 而不是论文里的启发式论证。

本仓库把现代神经网络架构（RNN、CNN、Transformer）背后的核心数学结论
形式化为可验证的证明。旗舰案例是 **LMT-twister**——*反事实表示瓶颈*，
涵盖容量计数与 IE / EHS 模型结构。

---

## 为什么做这个

神经架构通常用直觉或经验曲线来论证。本项目要求更严格的标准：一个结论
只有当 `lake build` 全绿、且证明中**不含 `sorry` / `admit` / `axiom`** 时才被接受。

核心主张（**第一性原理**）：

1. **RNN = 因果卷积**：线性递归展开后 `h(n+1) = Σ w^(n-k) x(k)`，
   与 CNN 共享群代数结构。
2. **CNN = 群代数乘法**：平移等变性就是乘法的结合律，不需要分析。
3. **Transformer 注意力 = 凸组合**：`softmax` 归一 ⟹ 输出在凸包内；
   置换等变 ⟹ 位置信息必须外部注入。
4. **容量 = 计数**：`R` 比特最多 `2^R` 个状态，区分 `V` 个动作需
   `≥ log₂V` 比特——这就是 LMT-twister 主定理 2.1 的离散骨架。

---

## 已形式化内容

全部位于 `LmPrinciple/`，并经 `lake build` 验证：

| 模块 | 内容 |
|---|---|
| `LmPrinciple/RNN.lean` | 线性 RNN 闭式解 = 因果卷积（任意 `CommSemiring` 上证明）；稳定性 `|w|<1 ⟹` 状态有界 `≤ M/(1-|w|)` |
| `LmPrinciple/CNN.lean` | 卷积 = 群代数乘法（`AddMonoidAlgebra ℝ ℤ`）；平移等变性 = 结合律；脉冲响应公式 |
| `LmPrinciple/Transformer.lean` | `softmax` 权重恒正 + 归一（凸组合）；自注意力置换等变 |
| `LmPrinciple/LMT.lean` | 容量计数（鸽巢原理）；复 SSM = RNN 复化；IE / EHS 模型结构（论文式 1/2） |
| `LmPrinciple.Fractal` | 分形的必要性（来自 `docs/wiki/shape.md`） |

> 截至 2026-08-12：`lake build` 全绿，16 条定理全部机器验证
> （mathlib 闭包 1758 模块源码编译）。

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
│   ├── index.md
│   ├── project-overview.md
│   ├── current-status.md
│   └── SCHEMA.md
├── scripts/              # Wiki 校验脚本 + 环境搭建
├── manifests/            # 原始资料登记（raw_sources.csv）
├── lakefile.toml         # 本地（离线）mathlib 物化
├── lean-toolchain        # leanprover/lean4:v4.21.0
└── README.md
```

知识分层为 **raw → wiki → code**：

- **raw**：原始资料（登记在 `manifests/raw_sources.csv`）
- **wiki**：编译后的当前共识（`docs/wiki/`，v2 schema）
- **code**：执行层（`LmPrinciple/`）

> 只改代码不回写 wiki，算没做完。

---

## 构建

环境要求：

- [elan](https://github.com/leanprover/elan) + Lean **4.21.0**
- mathlib **v4.21.0**（rev `308445d`，2025-06-30）

本仓库通过本地 `path` require（`lakefile.toml`）固定 mathlib 及其 8 个依赖，
构建时无需联网。克隆后：

```bash
lake build            # 真实 lake 二进制；Windows 见 scripts/run_build.sh
lake build LmPrinciple  # 只构建形式化部分
```

全新环境搭建见 `scripts/setup_mathlib.sh`（Windows 专用）与
`docs/wiki/current-status.md` 的"环境搭建流程"。

> ⚠️ 不要把 `lean-toolchain` 改回 `v4.34.0-rc1`——Batteries 语法不兼容，会编译失败。

---

## Wiki 系统（wiki-first）

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

> 凡是提到、收到、引用、保存的任何非代码文件 → 第一件事查
> `manifests/raw_sources.csv`。

---

## 状态与路线图

**已完成**

- ✅ Lean 4.21.0 + mathlib v4.21.0 环境，全离线物化
- ✅ RNN / CNN / Transformer / LMT 共 16 条定理机器验证
- ✅ Wiki-first 知识系统（v2 bootstrap，lint 全绿）

**待办**

- ⏳ LMT-twister 主定理 2.1 信息论证明（引理 A.1–A.4：IE 容量经 DPI → Fano → EHS）。
  mathlib 武器已确认就位：`Mathlib/InformationTheory/Hamming.lean`（Fano）与
  `Mathlib/InformationTheory/KullbackLeibler/`（互信息 + DPI）
- ⏳ 一般逐点卷积公式 `(f⋆g)(n) = Σ f(k)g(n-k)`
- ⏳ 按需 `.olean` 缓存，替代全量源码编译

---

## 来源

- LMT-twister 论文 `head-en.tex` / `head-zh.tex`（附录 A，引理 A.1–A.4）
- 架构概览：`docs/wiki/project-overview.md`
- 实时状态：`docs/wiki/current-status.md`

远程仓库：`git@github.com:logos-42/lm-principle.git`
