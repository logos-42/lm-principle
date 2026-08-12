---
title: lm_principle 当前状态
source: session
created: 2026-08-12
last_confirmed: 2026-08-12
audience: public
stage: current
schema_version: 2
tags: [status, lean, mathlib]
---

# lm_principle 当前状态

## 项目定位

用 **Lean 4 + mathlib v4.21.0** 形式化"大模型的数学第一性原理"，以
LMT-twister（反事实表示瓶颈）为核心案例，覆盖 RNN / CNN / Transformer 三大架构。

## 已完成

- ✅ **Lean 环境**: elan + Lean 4.21.0；mathlib v4.21.0（rev 308445d, 2025-06-30）
  手动物化：github.com 对进程内 libcurl 不可达 → SSH 克隆 + path require +
  8 个依赖固定同代 rev
- ✅ **编译验证 (2026-08-12)**: `lake build` 全绿，16 条定理全部机器验证
  （mathlib 闭包 1758 模块源码编译；.lake ≈ 1.1GB）
- ✅ **LmPrinciple/RNN.lean**: 线性 RNN 闭式解 = 因果卷积
  （任意 CommSemiring 上证明）；稳定性 |w|<1 ⟹ 状态 ≤ M/(1-|w|) 有界
- ✅ **LmPrinciple/CNN.lean**: 卷积 = 群代数乘法（AddMonoidAlgebra ℝ ℤ）；
  平移等变性 = 乘法结合律（左右两侧）；ℤ 上左右平移一致；脉冲响应公式
- ✅ **LmPrinciple/Transformer.lean**: softmax 权重恒正 + 归一（凸组合）；
  自注意力置换等变（Equiv.sum_comp 求和重排）
- ✅ **LmPrinciple/LMT.lean**: 容量计数（R 比特 ⟹ ≤2^R 状态；V=126 时 6 比特不够
  7 比特够；126/7 = 18× 节省）；复 SSM = RNN.rnn 复化（定理复用）；
  IE/EHS 模型结构形式化（论文式 1/2）
- ✅ **LmPrinciple/Fractal.lean (2026-08-12, 8 定理)**: 分形结构上的自由能
  下降速率推演——分形分配定理（预算前缀集中 ≥ 均匀平摊，核心）、残差收缩
  ⟹ 自由能指数下降、QKV 注意力凸组合误差界、MoE 凸组合误差界、分形维数
  D=log b/log(1/s) 尺度不变、连接密度幂律单调、fractal_beats_uniform 总定理
- ✅ **LmPrinciple/ArchCompare.lean (2026-08-12, 5 定理)**: RNN/CNN/LSTM 对比
  ——残差防坍缩（单层 + n 层: 距离 ≥ (1-c)^n 下界 = 高维结构不坍缩的严格
  证明）、LSTM 门控记忆保留 (c_t ≥ α^t·c_0 信息指数保留)、RNN 乘性记忆
  消失 (= 收缩特例, ≤ |w|^t 指数衰减)、对比总定理
- ✅ **LmPrinciple/Efficiency.lean (2026-08-12, 8 定理)**: 参数利用效率对比
  ——每参数交互率（注意力 n²/(3d²) vs RNN n, 反超条件 3d²<n）、注意力 vs CNN
  交互数、LSTM 门控保留上界、参数信息保留对比总定理、残差参数保留、
  分形参数分配效率
- ✅ **LmPrinciple/InfoDynamics.lean (2026-08-12, 12 定理)**: 信息动力学框架
  ——信息熵/交叉熵/KL/变分自由能定义、**Gibbs 不等式 KL≥0**（变分自由能
  非负 = 最小变分自由能原理）、交叉熵分解 CE=H+KL、交叉熵≥熵、信息质量流
  对比、信息流动速度（CNN≥RNN）、确定性防坍缩保证、FFN 可坍缩、回馈系数、
  hypothesis_verification 综合假设验证
- ✅ **LmPrinciple/Murray.lean (2026-08-12, 5 定理)**: C1 默里定律
  （守恒 ⟹ 比率 ρ³=1/2 即 0.79 被锁定 + 对称=维护最小）+ C2 最优深度
  存在条件（边际收益<边际成本 ⟹ 超阈值加深必然更差 + 最优深度存在 ≤ k₀+1）
- ✅ **LmPrinciple/Murray.lean §3-4 + Fractal.lean (2026-08-12, +6 定理)**: 三项成本完整变分证明
  （murray_variational_optimal 全局最小, 纯代数）+ 流量守恒 + C1 完整链 +
  C3 连接密度凸性 + C4 幂律收益 ⟹ 最优深度存在
- ✅ **总计: 60 条定理全部机器验证**（lake build 全绿, 无 sorry）
- ✅ **推送门禁 (lefthook)**: .lefthook.yml (pre-push: verify_all.sh +
  wiki_lint) + 手动 .git/hooks/pre-push 兜底——验证无错误才能推送
- ✅ **Wiki-first 系统**: 维基-llm v2 bootstrap（38 文件），wiki_lint 全绿
- ✅ **远程**: git@github.com:logos-42/lm-principle.git（SSH 已认证，已推送）

## 未完成 / 待办

- ⏳ **主定理 2.1 信息论证明**（**等用户假设，随时可开工**）: 引理 A.1（IE 容量，
  DPI）→ A.2（Fano）→ A.3/A.4（EHS）。数学库武器已确认就位:
  `Mathlib/InformationTheory/Hamming.lean`（Fano 不等式）+ 
  `Mathlib/InformationTheory/KullbackLeibler/`（互信息 + DPI）
- ⏳ **CNN 一般逐点卷积公式**: (f⋆g)(n) = Σ f(k)g(n-k)（Finsupp 双层和展开，
  非第一性原理必需，留 TODO）
- ⏳ **按需 olean 优化**: 并行会话验证过 `lake exe cache get <Module>` 可按需拉
  63 个 olean（870M），可替代全量源码编译（下次换环境时优先尝试）

## 环境搭建流程（2026-08-12 沉淀 · 可复现）

**问题链**: github.com 对 lake/elan 的进程内 libcurl 不可达（schannel 吊销检查
CRYPT_E_REVOCATION_OFFLINE + 间歇 TCP 阻断）→ 一切 lake 网络操作（Reservoir 解析、
cache 下载、tag 解析）全部失败。解法 = **全离线物化**：

1. **工具链**: `lean-toolchain` 固定 `leanprover/lean4:v4.21.0`（elan 已装）
2. **mathlib**: SSH 克隆到 `.lake/packages/mathlib`，checkout **原始 v4.21.0 提交
   308445d**（2025-06-30）。⚠️ 该 tag 后来被移动过：tag 上的 lake-manifest.json
   pin 的 8 个依赖是 4.34 时代 rev（与 lean 4.21 不兼容）——必须用
   `git log --lean-toolchain` 找到原始提交，取其**自己的** manifest 里的 dep rev
3. **8 个依赖**（batteries/Qq/aesop/proofwidgets/importGraph/LeanSearchClient/
   plausible/Cli）: SSH 克隆 + checkout mathlib@308445d manifest 里的精确 rev
   （全 4.21 时代，lean-toolchain 均 = v4.21.0）
4. **lakefile.toml**: mathlib + 8 依赖全部 `path` require → 解析完全离线，
   不需要 manifest / 网络 / Reservoir
5. **构建**: 用**真实 lake 二进制**（elan shim 启动即解析默认工具链 v4.33.0 未装
   → 尝试下载 → 假失败）: `~/.elan/toolchains/leanprover--lean4---v4.21.0/bin/lake.exe
   build`；前置 `MATHLIB_NO_CACHE_ON_UPDATE=1`（mathlib 的 post_update 钩子会拉缓存）

**脚本索引**（全部在 `scripts/`，Windows 专用）:
`setup_mathlib.sh`(环境总装) / `clone_deps.sh`(SSH 克隆依赖) /
`pin_v421.sh`(固定 308445d + 8 依赖 rev) / `run_build.sh`(真实 lake 构建) /
`deepen_mathlib.sh`(找原始提交)

## 形式化工作流（定理 → 机器验证）

1. **先写 statement 再写 proof**: 每个定理先有"第一性原理"叙述（文件头 docstring），
   证明是后验的
2. **最小 import 集**: 先跑 `LmPrinciple/Smoke.lean`（`#check` 全部要用的引理）
   编译闭包一次，正式文件增量编译快；引理名不确定 → 本地 grep
   `.lake/packages/mathlib/Mathlib/` 确认（2025 版 mathlib 的 API 与最新版差异大，
   `coeff_mul`/`not_injective_of_card_lt`/`geom_sum_eq` 等都不存在）
3. **编译迭代**: `lake build` 报错 → 按错误逐点修（典型: 引理不存在换路径、
   `omega` 需 `Finset.mem_range.mp` 喂范围事实、`rw` 不深入 binder 用
   `Finset.sum_congr`/`congrArg` 降级到点等式、不等式引理不能 `rw` 用 `exact`）
4. **验证标准**: `lake build` 全绿 + 扫描无 `sorry/admit/axiom` + 定理计数核对
5. **wiki writeback**: 结果/坑/方法写回 current-status + log，`wiki_lint --strict=v2` 通过

## 环境坑（本机 Windows）

- curl schannel 吊销检查失败（CRYPT_E_REVOCATION_OFFLINE）：lake 进程内 libcurl
  无法关闭 → 只能 git（SSH）物化 mathlib
- raw.githubusercontent.com / github.com 间歇不可达（无代理），SSH 协议可用
- 后台命令 UTF-16 BOM 污染 → 长命令写 .sh 脚本再执行
- lean-toolchain 别改回 v4.34.0-rc1（Batteries 语法不兼容，会编译失败）；
  `scripts/setup_mathlib.sh` 是 Windows 专用
- Lean 4.21 core 只有 omega；linarith/nlinarith/ring/field_simp 需
  `import Mathlib.Tactic.{Linarith, Ring, FieldSimp}`
- importGraph 仓库名带连字符 `import-graph`（≠ importGraph），克隆前先查 manifest
- `∑ x in s, f x` 记法已弃用（编译 warning）→ 用 `∑ x ∈ s, f x`
- elan shim（~/.elan/bin/lake.exe）默认工具链解析到 v4.33.0（未装）→ 假失败，
  一律用 `scripts/run_build.sh`（真实二进制）

## 相关文档

- 来源: LMT-twister 论文 head-en.tex / head-zh.tex（附录 A 引理 A.1-A.4）
- 架构: `docs/wiki/project-overview.md`
- 日志: `docs/wiki/log.md`
