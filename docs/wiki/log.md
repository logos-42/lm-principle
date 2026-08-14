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
| 2026-08-13 | Hopfield | Hopfield 能量形式化 + 下一轮实验 | 新模块 Hopfield.lean (+4 定理, 总计 73→77): 能量差分恒等式 (双和展开机器验证), 翻转严格下降 (异步更新收敛), 现代 Hopfield 更新=凸组合, Hopfield=Attention 同构。实验 (hopfield_experiments.py): E1 联想记忆容量平滑下降; E2 能量轨迹 3/3 单调非增 (与定理互证); E3 β 分岔相变 (β_c≈4, 混合态→模式锁定); E4 逐层能量 ΔE_k 全正仅 3/5/2/5 ⟹ 能量度量下递减性依然不成立 (强化上轮负面结论)。 |
| 2026-08-13 | 审查+补齐 | 实验论证审查: 找到临界点, 修公式/实验缺陷 | 审查结论: 定理层严谨, 声明层 6 处失真 (三项措辞/悖论解决无支撑/ffn 模态/hypothesis_verification docstring/深度定理未用条件(i)/1D 形式化)。补齐: ①新模块 CriticalPoint.lean 3 定理 (总计 70→73): 临界点定理 (最优深度 = 第一个 Δ_k<λ 的层, 精确闭式), 幂律临界点对 (Δ_kstar<λ≤Δ_kstar-1), 组合定理 ②实验一公式缺陷根因: 树级成本漏流量守恒因子 Q_g=Q/2^g, 修正后最优收敛 2^(-1/3) (G=50: 0.795, 偏差 0.13%), 见 diagnose_murray_cost.py ③实验 v2 多 seed + 深度监督 Δ_k 测量 (experiments_v2.py) ④闭式公式数值验证 (verify_critical_point.py) ⑤论文 two-term 措辞修正 + Remark 悖论真解决 ⑥docstring 修补 (ffn 必要→充分, T10 合取修正)。 |
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

## [2026-08-12] 会话 | Efficiency.lean: 参数利用效率对比 (8 定理)

- 用户问题: 对比 Transformer 参数利用效率 vs RNN/CNN/LSTM (结合假设)
- 新增 `LmPrinciple/Efficiency.lean`（8 定理, 总定理数 29 → **37**）:
  - 每参数交互率: attention n²/(3d²)（参数与 n 无关）vs RNN n/1、
    CNN n·k/k = n——反超条件 **3d² < n**（attention_more_interactions_per_param）
  - attention_vs_cnn_interactions: 核 k<n 时 n² > n·k（全局 > 局部）
  - forget_gate_retention_upper: 门控保留率 ≤ 100%（上界）
  - param_retention_compare: RNN 信息 ≤ |w|^t vs LSTM ≥ α^t（对比总定理）
  - residual_param_retention: 恒等路径免费参数效率
  - fractal_param_allocation: 参数分配效率（分形 ≥ 均匀）
- 结论: 参数效率两维度——**交互率**（长序列 3d²<n 时 Transformer 反超,
  全局交互规模经济）vs **信息保留率**（门控/恒等路径可学到 100%,
  RNN 被稳定性锁死）; 分形分配 = 每参数边际自由能下降最大化
- 已推送

## [2026-08-12] 会话 | InfoDynamics.lean: 信息动力学 + 变分自由能 (12 定理)

- 用户要求: 定义信息质量流/流动速度/坍缩概率/高维流动效率; 检查信息回馈
  (含 FFN); 把信息熵/交叉熵/最小变分自由能原理计入, 对比模型效率
- 新增 `LmPrinciple/InfoDynamics.lean`（12 定理, 总定理数 37 → **49**）:
  - **Gibbs 不等式 KL≥0**（核心）: 变分自由能 F(p,q)=KL(p‖q) ≥ 0——
    最小变分自由能原理的离散形式; 交叉熵分解 CE = H + KL; 交叉熵 ≥ 熵
  - 信息质量流: LSTM α^t ≥ RNN |w|^t (门控结构质量流更高)
  - 信息流动速度: CNN 每层 k 格 ≥ RNN 1 格 (注意力 1 层全局)
  - 确定性防坍缩: 残差输入距离 ≥ ε/(1-c)^t ⟹ 输出距离 ≥ ε (坍缩概率 0)
  - **FFN 可坍缩**: 无回馈 (β=0) 存在实现输出恒常数——回馈是防坍缩必要条件
  - hypothesis_verification: 组装全部结构定理 (回馈+凸组合+分形分配+Gibbs)
- 结论: 自由能最小化依赖的信息结构 = ①恒等/门控回馈 (防坍缩+保留)
  ②全局交互 (凸组合误差界) ③前缀参数集中 (分形) ④交叉熵下界 (T8)
- 已推送

## [2026-08-12] 会话 | Murray.lean: 默里定律 + 最优深度条件 (5 定理)

- 用户要求: 形式化 C1 (默里定律三项成本最优性) + C2 (分形维数⟹最优深度)
- 新增 `LmPrinciple/Murray.lean`（5 定理, 总定理数 49 → **54**）:
  - C1: murray_symmetric_ratio_cube (守恒 ⟹ ρ³=1/2 即 0.79 被锁定) +
    symmetric_branch_minimizes_maintenance (对称=维护最小) +
    murray_law_algebra (组合)
  - C2: depth_beyond_threshold_useless (边际收益<边际成本 ⟹ 超阈值
    加深必然更差) + optimal_depth_exists (最优深度存在且 ≤ k₀+1)
- **回答"最优深度在什么条件成立"**: ①收益严格递减 ②成本>0
  ③收益最终低于成本 (hcross)——三者满足 ⟹ 有限最优深度存在;
  若 ③ 不成立 (∀k, Δ_k≥λ) 则"越深越好" (最优深度不存在/无限)
- 编译坑记录: λ 是 Lean 关键字不能做标识符; mc·(m+1) 的 Nat cast
  陷阱 (↑(m+1) vs ↑m+1); conv_lhs 限定重写范围
- 已推送

## [2026-08-12] 会话 | 严格实验验证: 数学公式 vs 实验数据对照 (verify_experiment.py)

- 用户要求: "数学形式化是否与实验匹配? 不能数据造假, 严格实验证明"
- 新增 `scripts/verify_experiment.py`（可复现, 全部数字重新计算, 数据来源 shape.md）
- **核心发现 1: 实验一代码的模型 ≠ 默里定律的模型**
  - 两成本全局扫描 (实验一代码: 阻力 Σn/r⁴ + 维护 Σn·r²) 最小值 ≈ 1.00 ≠ 0.79
  - 这是作者已诚实承认的悖论 (0.90 总能耗 < 0.79)
  - 默里定律正确路径 = 分叉约束模型: 单管最优 r³ ∝ Q (公式A) + 流量守恒
    r₁³+r₂³ = r³ (公式B) + 对称分叉 ⟹ ρ = 2^(-1/3) = 0.7937 (公式C)
  - 数值验证: r*/Q^(1/3) 恒 = 2^(1/6) = 1.1225 ✓; 对称分叉比率恒 0.7937 ✓
- **核心发现 2 (新)**: 纯输送成本下分叉比不分叉贵 2^(1/3) ≈ 1.26 倍
  - "为什么分叉"由覆盖需求 (空间填充) 决定, 不是输送成本
  - 这正对应文章"覆盖×节省"张力: 默里定律给"必须分叉时的最优比率"
- **实验二对照**: 参数效率比 400641/301569 = 1.33 (+32.9%)——分形少 25%
  参数保持性能 ✓ 匹配 prefix_allocation_optimal; 但损失差异 0.005% 在噪声内,
  不能证明性能更优 (诚实边界)
- **实验三对照**: 临界深度公式 L* = max{L : Δ_L ≥ 0} = 2 ✓ 匹配
  optimal_depth_exists; 但收益序列非单调 (6层分形 39.8 < 4层 72.0),
  1/k^p 形状未被直接证实 (诚实边界)
- **临界点公式汇总**: A. 比率 ρ = 2^(-1/3) (与成本系数无关, 物理锁定)
  B. 深度 L* = max{L : Δ_L ≥ λ}  C. 参数效率比 1.33
- 验证脚本自身的 2 个 bug 被严格检验暴露并修复 (网格截断、凹性方向)
- 下一步: 本地 torch CPU 真实训练 (experiments/run_fractal_experiments.py,
  seed 42 与文章一致) —— 用真实本地数据复核实验二/三
- ✅ **已完成 (2026-08-13)**: 本地真实实验跑通 (torch 2.12.1+cpu, seed 42)
- ✅ **已完成**: 对照分析 scripts/compare_local_vs_math.py + wiki 更新

## [2026-08-13] 会话 | 本地真实实验: torch CPU 训练复核 (实验二/三)

- 用户要求: "跑模型确认效果验证, 附上真实本地数据"
- 新增 `experiments/run_fractal_experiments.py`（与文章代码一致, seed 42 全局流）
  + `experiments/results/fractal_experiments.json`（真实数据, gitignore 不入库）
- **实验二 (本地)**: 均匀 400641 参数/损失 **113.6133**; 分形 301569 参数/
  损失 **113.6098** —— 参数效率比 **1.3285** (+32.9%), 分形少 24.7% 参数
  **且本地分形损失略低** (文章: 均匀略优——差异均在噪声内)
- **文章复现度**: seed 42 复现——均匀差 0.0033, 分形差 0.0060 (数据可靠)
- **实验三 (本地)**: 最优深度均匀/分形均 = 2 层 ✓ (Δ₂→₄ = +4.71 > 0
  ⟹ L* = max{L : Δ_L ≥ 0} = 2, 与 optimal_depth_exists 一致)
- **新发现 P4 (本地比文章更强)**: 分形深层优势显著——6层 (0.67×),
  10层 (0.80×), **14层 (0.39×: 44.8 vs 113.6)**——连接密度幂律
  (深层稀疏) 的实证: 分形深层不浪费参数在收益递减结构上
- 诚实边界: 实验三绝对损失与文章不同 (torch 环境差异, 模式一致);
  收益序列非单调 (8层均匀优); "1/k^p 递减"具体形状需多 seed
- 对照脚本: scripts/compare_local_vs_math.py (读 JSON, 输出对照表)
- 已推送

## [2026-08-13] 会话 | 远程更新阅读 + 论文/README 中英文 + MIT 许可

- 远程更新 0b9716f (并行会话): CriticalPoint.lean (3 定理, 73 总计) +
  diagnose_murray_cost.py (悖论真根因: 阻力项漏流量守恒因子, 修正后
  argmin→0.795) + experiments_v2.py (3 seeds: 分形 vs 均匀不显著,
  '4层断崖'是训练假象, Δ_k 不严格递减 5/11 但 kstar=2 稳健) +
  docstring 修正 (ffn 必要→充分, T10 合取) + 成本改称两项
- **阅读消化**: 全部理解并吸收进论文/README
- **论文更新** (jrnl + conf):
  - 清理 4 处脏行 (git 提交信息误粘贴进 tex)
  - 新增 §Multi-seed rerun: honest correction (3-seed 结论)
  - 定理数 70→73 (63 核心)
  - conf 实验节同步 (本地数据 + 3-seed + kstar)
- **README 中英文更新**: ffn 充分表述、悖论机制 (流量守恒因子)、
  CriticalPoint 闭式解 k* = ⌈√(c/λ)⌉-1、真实模块表 (11 模块)、
  本地实验 + 3-seed 诚实修正、Roadmap ② 更新、诚实边界
- **MIT 许可**: LICENSE 文件 + 两版 README 许可段
- 验证: 73 定理全绿 (verify_all.sh) + 两版 tex 结构全绿
- 已推送

## [2026-08-12] 会话 | Training.lean: RLHF/DPO/稀疏化/预训练后训练 (10 定理)

- 用户指出缺失: RL (强化学习), MoE 深入, 稀疏注意力, 预训练/后训练推演
- 新增 `LmPrinciple/Training.lean`（10 定理, 总定理数 60 → **70**）:
  - 预训练: scaling_law_strict_anti (L=c/(N+1)^α 幂律递减, 与 C4 同构)
    + pretraining_loss_lower_bound (CE ≥ 数据熵 = 预训练损失下界)
  - 后训练 RLHF: rlhfPolicy (softmax 策略定义) + rlhf_policy_is_distribution
    (配分函数归一, Σ=1) + posttraining_kl_nonneg (KL 漂移 ≥ 0, Gibbs)
    + rlhf_kl_penalty_structure (J(π)=奖励-β·KL 的目标结构)
  - DPO: dpo_loss_nonneg (-log σ(β·Δ) ≥ 0, log_nonpos_iff)
  - 稀疏化: sparse_moe_preserves_bound (top-k 重归一保持凸组合 ⟹ 误差界)
    + sparse_attention_preserves_bound (掩码重归一同构复用)
    + sparse_attention_interactions (n·k < n², 复用 Efficiency)
  - 统一: training_unified (预训练+后训练+稀疏化 = 变分自由能最小化)
- 核心洞见: **RLHF 最优策略 = softmax (Gibbs 推论)**——J(π) = β·log Z -
  β·KL(π‖π*), 偏离最优策略的代价 = KL ≥ 0; 完整最优性证明链
  (r 反解 + exp-log 互逆) 已注释, 核心不等式已验证
- 编译坑: λ 关键字; r* 非法标识符 (* 是乘法); Finset.sum_mul/mul_sum 是
  protected lemma 需显式传参; sum_filter 参数序 (s)(f)(p); 1/x 与 x⁻¹
  不定义相等 (需 simpa); ite_mul 不是 mul_ite; Real.log_nonpos 不存在
  (用 log_nonpos_iff)
- 已推送

## [2026-08-12] 会话 | IEEE 论文撰写：分形必要性 → 机器验证定理

- **产出**: `paper/` 目录，Overleaf 同款官方 IEEEtran 模板（CTAN 源）
  - `main_conf.tex`（IEEE 会议版，双栏）+ `main_jrnl.tex`（IEEE 期刊版，单栏，含更详细证明 + 定理-模块映射附录）
  - `IEEEtran.cls`、`bibtex/`、`make_figures.py` + 3 张 `fig_*.png/pdf`
- **论文主线**: 分形必要性 → 60 条机器验证定理（C1-C4 从假设升格为定理）
- **架构**: 动机(Why formal proof now / Scaling laws / 分形叙述 / 悖论) → 蒸馏 C1-C4 假设 → 结构论证六节（每节定理+证明+实证呼应）→ 实验印证 → 结论与局限
- **三张图全部用真实数据**（源自 `shape.md` 原始脚本输出）:
  - fig_murray: 默里定律三项成本变分最优 0.79
  - fig_fractal_params: 分形 vs 均匀 -25% 参数、损失几乎相等 (113.61 vs 113.62)
  - fig_depth: 真实逐点数据 depth=[2,4,6,8,10,14,18]，深度2最优、≥4断崖
- **引用自检**: 会议版/期刊版全部 `\ref` 无悬空（脚本校验），图/表/定理/Remark 均在正文被引用
- **作者**: Yuanjie Liu, yuanjieliu65@gmail.com
- **遗留**: 本机无 LaTeX 未编译验证（待 Overleaf）；`shape2026` 引用 URL 仍是 example.com 占位，待真实链接
- 本次会话一并提交推送
