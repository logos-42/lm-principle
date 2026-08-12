---
title: Wiki 日志
source: session
created: 2026-08-12
last_confirmed: 2026-08-12
audience: public
stage: current
schema_version: 2
---

# Wiki 日志

| 日期 | 类型 | 主题 | 要点 |
|------|------|------|------|
| 2026-08-12 | 启动 | 初始化知识系统 | 建立 wiki、manifest、检查脚本和 repo 级默认规则。 |
| 2026-08-12 | 环境 | mathlib 按需配置 | 修正 lean-toolchain v4.34.0-rc1→v4.21.0（匹配 mathlib rev 308445d，见 setup_mathlib.sh）；按需 olean：`lake exe cache get <Module>`，全量 1.5GB+ → 按需 63 个文件（.lake 共 870M）；项目 lake build 通过，omega/norm_num 可用。 |

## [2026-08-12] 会话 | 形式化 RNN/CNN/Transformer + LMT 第一性原理

- Lean 4.21.0 + mathlib v4.21.0 环境就绪（mathlib 手动物化: SSH 克隆 +
  path require + 固定 mathlib 原始 v4.21.0 提交 308445d + 8 个依赖同代 rev）
- 新增 4 个定理模块: RNN（闭式解=因果卷积, 稳定性）、CNN（卷积=群代数乘法,
  平移等变=结合律）、Transformer（softmax 凸组合, 置换等变）、
  LMT（容量计数 pigeonhole, 复 SSM=RNN, IE/EHS 结构）
- ✅ **`lake build` 全绿: 16 条定理机器验证**（数学库闭包 1758 模块源码编译）
- 已推送 github:logos-42/lm-principle
- 待办: 主定理 2.1 信息论证明（等用户假设）
- 阅读 LMT-twister 仓库: AGENTS.md wiki-first 约定、current-status.md、
  论文 head-en.tex / head-zh.tex（附录 A 引理 A.1-A.4）

## [2026-08-12] 会话 | 流程方法沉淀

- current-status.md 新增两节: 「环境搭建流程（可复现）」（全离线物化 5 步 +
  脚本索引）、「形式化工作流」（statement→编译迭代→验证→writeback）
- 坑清单扩充: import-graph 连字符、∑ 记法弃用、elan shim 假失败

## [2026-08-12] 会话 | 收尾确认

- 早期后台进程回执全部消化（均为已被取代的方案，无遗留）
- 磁盘确认: 无 v4.34.0-rc1 残留工具链（下载被中断未落盘），5 个工具链
- **InformationTheory 模块就位确认**: `Hamming.lean`（Fano 不等式 →
  引理 A.2）+ `KullbackLeibler/`（互信息 + DPI → 引理 A.1），主定理 2.1
  证明的数学库武器已齐
- 下一步: 等待用户提供假设 → 形式化引理 A.1-A.4 + 主定理 2.1

## [2026-08-12] 会话 | 收录 shape.md（分形必要性）+ 编译页

- 用户提供第三季第3期文章 `docs/wiki/shape.md`（默里定律 + 分形 +
  分形Transformer + 最优深度），登记 raw 清单 + 补 v2 frontmatter
- 新建编译页 `docs/wiki/fractal-necessity.md`: 三条法则 + 三实验数据 +
  诚实边界（简化模型缺心脏做功项）+ **候选可形式化命题 C1-C4**
  （默里定律最优性 / 分形维数-深度关系 / 连接密度幂律 / 深度收益递减）
- C2 与 LMT-twister V34 发现呼应（训练容量可规模破解, 泛化独立封顶）
- 下一步: 用户确认假设 → 在 Lean 中形式化 C1-C4 或主定理 2.1

## [2026-08-12] 会话 | Fractal.lean: 分形自由能下降速率 Lean 推演 (8 定理)

- 用户假设: QKV+残差+MoE 在分形结构上自由能下降速率是否更高? 高维数学机制?
- 新增 `LmPrinciple/Fractal.lean`（8 定理全绿, 总定理数 16 → **24**）:
  ① prefix_allocation_optimal（收益递减 ⟹ 预算前缀集中 ≥ 均匀平摊——分形
  比均匀快的严格证明）② residual_contraction_decay ③ free_energy_exponential_decay
  ④ attention_error_bound（QKV 凸组合误差界）⑤ moe_error_bound ⑥
  fractal_dimension_scale_invariant ⑦ connection_density_strict_anti ⑧
  fractal_beats_uniform
- 结论: **是——只要每层下降量严格递减, 分形组织总下降 ≥ 均匀堆叠**;
  高维机制 = 凸组合(凸包) + 收缩映射(指数衰减) + 幂律稀疏((1-d)^(D-1))
- 已推送

## [2026-08-12] 会话 | ArchCompare.lean: RNN/CNN/LSTM 对比 + 不坍缩验证 (5 定理)

- 用户假设: 对比 RNN/CNN/LSTM; 运行中高维结构不坍缩且信息流动最高效?
- 新增 `LmPrinciple/ArchCompare.lean`（5 定理, 总定理数 24 → **29**）:
  - `residual_no_collapse` / `_n`: 残差防坍缩——收缩残差 ⟹ 输出距离
    ≥ (1-c)^n·输入距离 (**不坍缩到单点**的严格证明)
  - `lstm_memory_retention`: 遗忘门 α ⟹ 旧信息保留 α^t 比例 (指数保留)
  - `rnn_memory_decay`: RNN = 收缩特例 ⟹ 信息 ≤ |w|^t 指数消失
  - `lstm_beats_rnn_retention`: 对比总定理 (门控 vs 乘性记忆)
- 结论: **不坍缩** = 残差恒等路径保证 (纯乘性网络可能坍缩);
  **信息高效** = 门控/恒等路径损失率可学习 (α→1 零损失, vs RNN 固定 1-|w|)
- 新第一性原理问题: P4 最优信息传播 (Lipschitz 预算下残差最优, 待信息论定义);
  P5 距离下界 (1-c)^n × 容量 2^R 组合 (待)
- **推送门禁**: .lefthook.yml (pre-push: lake build + 无 sorry + wiki_lint)
  + 手动 .git/hooks/pre-push 兜底 (本机 choco/winget 无 lefthook 包)
- 已推送
