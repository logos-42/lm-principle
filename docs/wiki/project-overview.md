---
title: lm_principle 项目概述
source: session
created: 2026-08-12
last_confirmed: 2026-08-12
audience: public
stage: current
schema_version: 2
tags: [overview, lean, llm-math]
---

# lm_principle 项目概述

## 目标

把"大模型的数学第一性原理"写成可机器验证的 Lean 4 定理，
而不是论文里的启发式论证。核心主张：

1. **RNN = 因果卷积**: 线性递推展开后 h(n+1) = Σ w^{n-k} x(k)，
   与 CNN 共享群代数结构；
2. **CNN = 群代数乘法**: 平移等变性是乘法的结合律，不需要分析；
3. **Transformer 注意力 = 凸组合**: softmax 归一 ⟹ 输出在凸包内；
   置换等变 ⟹ 位置信息必须外部注入；
4. **容量 = 计数**: R 比特最多 2^R 个状态，区分 V 个动作需 ≥ log₂V 比特
   —— LMT-twister 主定理 2.1 的离散骨架。

## 工作流

- 用户写假设（反事实表示瓶颈的 IE vs EHS 定理）→ Lean 验证
- wiki-first：结论写回 `docs/wiki/`（维基-llm v2 schema）
- compile-first：所有定理必须 `lake build` 通过，不用 sorry

## 目录

- `LmPrinciple/RNN.lean` — 线性 RNN 闭式解 + 稳定性
- `LmPrinciple/CNN.lean` — 卷积代数 + 平移等变性
- `LmPrinciple/Transformer.lean` — softmax + 注意力置换等变
- `LmPrinciple/LMT.lean` — 容量计数 + 复 SSM + IE/EHS 结构
- `docs/wiki/` — 知识系统（v2 schema）
- `scripts/` — wiki 校验脚本 + setup_mathlib.sh

## 环境

- Lean 4.21.0（elan，~/.elan/bin）+ mathlib v4.21.0
- 远程: git@github.com:logos-42/lm-principle.git
