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
- ✅ **Wiki-first 系统**: 维基-llm v2 bootstrap（38 文件），wiki_lint 全绿
- ✅ **远程**: git@github.com:logos-42/lm-principle.git（SSH 已认证，已推送）

## 未完成 / 待办

- ⏳ **主定理 2.1 信息论证明**: 引理 A.1（IE 容量，DPI）→ A.2（Fano）→
  A.3/A.4（EHS）——等待用户提供假设 + mathlib InformationTheory API
- ⏳ **CNN 一般逐点卷积公式**: (f⋆g)(n) = Σ f(k)g(n-k)（Finsupp 双层和展开，
  非第一性原理必需，留 TODO）
- ⏳ **按需 olean 优化**: 并行会话验证过 `lake exe cache get <Module>` 可按需拉
  63 个 olean（870M），可替代全量源码编译（下次换环境时优先尝试）

## 环境坑（本机 Windows）

- curl schannel 吊销检查失败（CRYPT_E_REVOCATION_OFFLINE）：lake 进程内 libcurl
  无法关闭 → 只能 git（SSH）物化 mathlib
- raw.githubusercontent.com / github.com 间歇不可达（无代理），SSH 协议可用
- 后台命令 UTF-16 BOM 污染 → 长命令写 .sh 脚本再执行
- lean-toolchain 别改回 v4.34.0-rc1（Batteries 语法不兼容，会编译失败）；
  `scripts/setup_mathlib.sh` 是 Windows 专用
- Lean 4.21 core 只有 omega；linarith/nlinarith/ring/field_simp 需
  `import Mathlib.Tactic.{Linarith, Ring, FieldSimp}`

## 相关文档

- 来源: LMT-twister 论文 head-en.tex / head-zh.tex（附录 A 引理 A.1-A.4）
- 架构: `docs/wiki/project-overview.md`
- 日志: `docs/wiki/log.md`
