---
title: lm_principle 当前状态
source: session
created: 2026-08-12
last_confirmed: 2026-10-21
audience: public
stage: current
schema_version: 2
tags: [status, lean, mathlib]
---

# lm_principle 当前状态

## 项目定位

用 **Lean 4 + mathlib v4.35.0** 形式化"大模型的数学第一性原理"，以
LMT-twister（反事实表示瓶颈）为核心案例，覆盖 RNN / CNN / Transformer 三大架构。

## 已完成

- ✅ **Lean 环境**: elan + Lean 4.35.0；mathlib v4.35.0（rev 56a0058, 2026-10-13, tag
  v4.35.0）。当前工作机 macOS（darwin）：github.com 可达、elan 已装 v4.35.0；
  `.lake/packages/*` 以符号链接指向 `../NavierStokesAndEuler/.lake/packages/*`
  （该集已是 v4.35.0 同代 rev：mathlib 56a0058 + batteries/Qq/aesop/proofwidgets/
  importGraph/LeanSearchClient/plausible/Cli 均 2026-10 时代）
- ✅ **v4.35 迁移 (2026-10-20)**: `lean-toolchain` v4.21.0 → v4.35.0，mathlib
  308445d → 56a0058（tag v4.35.0）；`lake build` 全绿，83 条定理无 sorry。破坏性变更修复：
  `∑ k in s` 记法被**移除** → `∑ k ∈ s`（9 文件 104 处）；`abs_add` → `abs_add_le`
  （RNN/ArchCompare）；`AddMonoidAlgebra.single_mul_apply` →
  `AddMonoidAlgebra.coeff_single_mul_apply` + `.coeff` 取值（CNN）；
  `Finset.sum_eq_add_sum_diff_singleton` 移除 → `Finset.add_sum_erase`（Hopfield 5 处）；
  `field_simp` 现闭合更多目标 → 删冗余 `ring`（Fractal/Hopfield/Murray）；
  `simpa using hmul` 除法/乘积形式不匹配 → 加 `div_eq_mul_inv`（Murray/Training）；
  `mul_lt_mul_left` 需 `MulRightStrictMono` → 改 `mul_lt_mul_of_pos_left/right` +
  `lt_of_lt_of_eq`（Efficiency）；`Mathlib.Data.Real.Basic` → `Mathlib.Basic.Real.Basic`（12 文件）
- ✅ **v4.35 lint 清零 (2026-10-20)**: 迁移后残留警告全部消除，`lake build` 与
  `lake build LmPrinciple` 均 **0 error / 0 warning**（含 `rm -rf` 后的干净重建）。
  - **module-system 警告**：本库无 module 头但依赖 `requiresModuleSystem := true` 的
    mathlib → `lakefile.toml` 中 `[[lean_lib]] LmPrinciple` 加 `allowNonModules = true`
  - **unused-variable (13 处)**：全部是"证明比定理声明更强"的情形（如 `hc1 : c < 1`
    实际由 `hcont` 蕴含即可证）。保留公开签名的语义契约位，改名为 `_hc1`/`_hc0`/
    `_hmc`/`_hβ`/`_hΔ`/`_ha`/`_hsum`/`_hS`/`_hb`/`_hd1`/`_hc0` 前缀（ArchCompare /
    CriticalPoint / Fractal / Hopfield / Murray / Training）
  - **info 级提示**：`ring` 在 `convert` 后无法闭合目标 → 改 `ring_nf`（ArchCompare 2 处）；
    `Finset.card_le_univ` → `simp [Fintype.card_fin]`（Hopfield）；`if_pos/if_neg` →
    `ite_eq_left/ite_eq_right`（Training）；`haveI : Nonempty (Fin n)` → `have hne`
    （Transformer / Hopfield）；`simpa using (Real.log_inv x)` → `simp`（InfoDynamics）；
    `Mathlib.Data.Complex.Basic` → `Mathlib.Basic.Complex.Basic`（Smoke / LMT）；
    `simpa using hdecay` → `exact hdecay`（ArchCompare）
  - 剩余仅 2 条 `info`（ArchCompare 的 `CNN.single_mul_apply` / `RNN.rnn_closed_form`
    两个 `#check` 的刻意输出），非警告
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
- ✅ **本地真实实验验证 (2026-08-13)**: experiments/run_fractal_experiments.py
  (torch 2.12.1+cpu, seed 42, 与文章代码一致) + scripts/compare_local_vs_math.py
  —— 实验二: 分形 301569 参数/损失 113.6098 vs 均匀 400641/113.6133
  (效率比 1.33, 文章 seed 42 复现差 < 0.01); 实验三: 最优深度均 2 层
  (Δ₂→₄>0 ⟹ L*=2 ✓); 分形深层优势显著 (14层 0.39×); 诚实边界已记录
- ✅ **LmPrinciple/CriticalPoint.lean (2026-08-13, +3 定理)**: 临界点定理——
  **最优深度 = 第一个边际收益跌破成本的层** (C2 闭式解, 回答"临界点在哪"):
  `optimal_depth_is_first_crossing` (Δ 严格递减 + λ>0 + 最终跌破 ⟹
  kstar = Nat.find (fun k => Δ k < mc) 是最优深度, ∀L, N(L) ≤ N(kstar)) +
  `power_law_critical_pair` (幂律 Δ_k=c/(k+1)² 的跌破点满足
  Δ_kstar < λ ≤ Δ_kstar-1, 两侧夹逼) + `power_law_optimal_depth_is_critical` (组合)
- ✅ **LmPrinciple/Hopfield.lean (2026-08-13, +4 定理)**: Hopfield 能量最小化
  形式化 (hopfile.md 驱动) —— `energy_difference` (能量差分恒等式:
  E(s')-E(s) = (s_i-s'_i)·net_i, 对称权重+无自环, 双和展开机器验证) +
  `flip_energy_strictly_decreases` (翻转 ⟹ 能量严格下降 = 异步更新收敛保证)
  + `hopfield_update_convex_combination` (现代 Hopfield 更新 = softmax 凸组合,
  复用 Transformer) + `hopfield_update_eq_attn` (Hopfield 检索 = Transformer
  attention 同构)
- ✅ **Hopfield 实验 (2026-08-13)**: scripts/hopfield_experiments.py ——
  E1 联想记忆容量 (P/N: 0.05→1.0, 0.2→0.80, 0.3→0.72 平滑下降);
  E2 能量轨迹 3 trials 全单调非增 (与 flip_energy_strictly_decreases 互证);
  E3 **β 分岔相变** (β<3.6 混合态 0.888, β≈4.3 跃迁, β≥9.6 模式锁定 1.000);
  E4 逐层 Hopfield 能量 ΔE_k 全正仅 3/5 (β=1) / 2/5 (β=10) ⟹ **能量度量下
  依然不递减**——强化上轮结论: 最优深度定理的"收益严格递减"前提在
  真实网络 (loss 度量 + 能量度量) 下均不成立
- ✅ **LmPrinciple/Hopfield.lean β 分岔定理 (2026-08-13, +2 定理, 总计 77→79)**:
  `softmax_weight_concentration` (得分差 ≥ Δ ⟹ 非目标权重 w_j ≤ e^{-Δ},
  无需极限论证的定量集中性) + `hopfield_retrieval_error_bound` (检索锁定
  误差界: |x_new - X_i| ≤ n·e^{-βΔ}·M——β/Δ 增大 ⟹ 指数锁定, E3 实验
  β≥9.6 重叠=1.000 的理论形式; 凸组合权重集中 + 三角不等式)
- ✅ **Hopfield 实验扩展 (2026-08-13)**: scripts/experiments_h2.py ——
  E5 **β_eff×深度扫描**: 每层实际逆温度 β_eff = logit spread 深层单调更集中
  (depth8: 0.64→7.85; depth4: 0.95→6.18), 深度越大进入锁定区 (β>β_c≈4) 的
  层越多; ΔE_k 依然不递减 (全正 0/1, 2/3, 2/5, 4/7); 弱观察: β_eff 峰值层
  与正能量下降层重合 (depth6 层5 +0.344, E6 层3 +0.049)。
  E6 **字符级 LM 重测 ΔE_k** (真实文本语料, vocab=91, test loss 3.30 vs
  随机基线 4.51——真实学习): ΔE_k 全正仅 1/3 (β=1 和 10) ⟹ **排除合成任务
  伪影, 负面结论在真实 LM 上成立**。诚实标注: E5 模型欠训练 (full-batch),
  E6 单 seed。
- ✅ **LmPrinciple/Maxwell.lean (2026-08-13, +4 定理, 总计 79→83)**: 麦克斯韦
  方程 × 现有数学 —— 1D 周期格点 (ZMod N, 真模减法——修正 Fin 截断减法缺陷):
  `cross_term_zero` (交叉项 telescoping: 离散乘积法则 Σ(ΔE)B+ΣE(ΔB)=0) +
  `maxwell_energy_conservation` (无质量场能量守恒 dH/dt=0) +
  `massive_energy_decay` (质量项 dH/dt=-m²ΣE²) +
  `massive_energy_non_increasing` (能量非增预言)。
  **预言**: 用户假设 m_G=√3·M₀ ⟹ 能量时间常数 τ_G = 1/(6M₀²) (条件性预言,
  论文 §sec:maxwell)。诚实标注: 验证的是格点代数能量结构, 连续极限待 Analysis。
- ✅ **E7 判定实验 (2026-08-17)**: scripts/experiments_e7.py —— 真实语料
  (200K 字符, vocab=1147) + 12 层深度监督 + 3 seeds: Δ₁=+2.95, Δ₂=+0.42
  (合成任务此处 -2.24), 此后 ±0.17 噪声震荡; 递减一致性 6/11=55%。
  **结论**: ①合成任务的"Δ_k 证伪"是任务饱和伪影 (任务无深度收益, 线性
  可解), 真实任务确有连续深度收益 ②"严格递减"前提对真实网络过强——
  真实给"近似递减+噪声" ③H100 核心指标改为"递减一致性随规模的单调性"
- ✅ **H100 算力评估 (2026-08-17)**: scripts/estimate_h100_budget.py ——
  350M 全套矩阵 19 模型 = 373 卡时/$933/1.5 天 (10 卡); 1.3B = $4623/
  7.7 天; 7B = $124K/207 天 ✗。推荐 P0 深度扫描 + P1 β_eff 并入同批
  模型, 核心判定二值 (递减一致性 >70%=规模恢复, ≈50%=真证伪)
- ✅ **总计: 83 条定理全部机器验证**（lake build 全绿, 无 sorry）
- ✅ **推送门禁 (lefthook)**: .lefthook.yml (pre-push: verify_all.sh +
  wiki_lint) + 手动 .git/hooks/pre-push 兜底——验证无错误才能推送
- ✅ **Wiki-first 系统**: 维基-llm v2 bootstrap（38 文件），wiki_lint 全绿
- ✅ **2026-08-13 审查与补齐**: 用户要求"找到临界点, 修公式/实验缺陷"——
  - **临界点 (C2 闭式解)**: CriticalPoint.lean 3 定理——最优深度 =
    第一个边际收益跌破成本的层 kstar = Nat.find (fun k => Δ k < mc),
    幂律临界对 Δ_kstar < λ ≤ Δ_kstar-1 (闭式 kstar = ⌈√(c/λ)⌉-1,
    数值验证 8 组全过, 含一般 α)
  - **公式缺陷诊断** (scripts/diagnose_murray_cost.py): 实验一树级成本
    漏流量守恒因子 Q_g=Q/2^g ⟹ 原公式 argmin 在边界 ρ→1 (0.9<0.79);
    修正后内点最优收敛 2^(-1/3) (G=50: 0.795, 偏差 0.13%)——悖论真根因
  - **实验 v2** (scripts/experiments_v2.py, 3 seeds):
    · 深度监督 Δ_k 测量: Δ_1=+123.8, Δ_2=-2.24 (加层变差), 此后 ±0.2 波动,
      Δ 递减一致性仅 5/11 ⟹ **真实 Δ_k 不严格递减**——定理假设在实验中被证伪,
      交叉点 kstar=2 对任意 λ 成立 (第 2 层起负收益)
    · 独立深度扫描: depth2=0.79±0.06 最优 (稳健), depth6=1.28<depth4=1.67
      ⟹ "≥4 断崖"不成立 (多 seed 下深模型可学习)
    · 分形 vs 均匀 (mini-batch 修正): uniform=86.8±47.2, fractal=75.7±52.9
      ⟹ 原单 seed 113.61/113.62 是训练平台巧合, 对比不显著
  - **诚实结论**: 定理逻辑正确 (if Δ 严格递减 + 跌破 ⟹ kstar 最优);
    实验数据不满足定理前提 (Δ_k 非单调) ⟹ 论文把实验改标为
    "structural statement, 测量见 v2", 并修正三项措辞/ffn 模态/T10 docstring
- ✅ **远程**: git@github.com:logos-42/lm-principle.git（SSH 已认证，已推送）。
  **2026-10-20 已推送 commit 3cbc84a**（认知动力学立项: 公设体系 + L6/五组件推导
  + E8-E12 实验 + 94 定理, 27 files +3162 行）

## 认知动力学工作线（2026-10-20 启动 · 同日定调牛顿秩序）

**目标**: 完全从数学上解释 AI 大模型的设计原理。**方法论（用户 2026-10-20 定调）**:
不走"从经验假说（如权重子空间）反推智能起源"的路线；走牛顿秩序——
**先定本体（结构/感知/比特三元组）→ 设公设（A1-A4）→ 推数学（率-失真/信息论/
谱理论/不动点）→ 验基本假设（L1-L5）**。关键立场: 这是"智能的结构"不是"力学
结构"——无外部认知力、无固定背景几何、几何被演化生成（信息性机制, 非几何曲率）。
框架页: `docs/wiki/cognitive-dynamics.md`。

- ✅ **公设体系已立**:
  - A1 组合本体公设（智能存在于算子组合, 不在单元; 数学化 = VC 维/覆盖数）
  - A2 感知压缩公设（感知 = 率受限保信息压缩; 数学形式 = Shannon 率-失真 R(D)）
  - A3 信息度量公设（H/I(·;·)/KL 为统一货币; 自认边界: 比特不给意义）
  - A4 落差驱动公设（运动定律: Δs ∝ -∇_s D(s); 在线形式 = next-token 惊奇下降;
    自认与 FEP/预测编码/SGD 同构, 新意在从 A1-A3 推必然性）
- ✅ **定律清单 L1-L5**: L1 组合必然性 / L2 规模律（损失 ≥ 残余失真+不可约熵,
  幂律来自感知流谱尾）/ L3 吸引子与临界（不动点=二阶矩谱主子空间,
  Lyapunov<0 有序, 可学习需边缘稳定）/ L4 最优深度有限 / L5 预测原理（MDL）
- ✅ **L4 已 Lean 证明**: `optimal_depth_is_first_crossing`（Murray/CriticalPoint）——
  认知动力学第一条机器验证定律
- ⏳ **R1 定律推导**: L2/L3 纸上推导草稿（先数学后 Lean）
- ✅ **公设独立性分析完成** (`docs/wiki/axiom-independence.md`): 原 A1-A4 极小化为
  **3 定义 + 2 公设 + 1 容量引理**。核心发现: A4 可三分解——目标函数（经
  Solomonoff 遗憾界可从 A2+A3 推: 持存结构累积落差≈可达最小）+ 下降方向
  （陡降定理，数学事实）均可推导；不可还原残核 = **选择原理**（持存过滤器），
  即牛顿第一定律（惯性）的类比物: 单独近于重言，靠锚定的 L2-L5 定理体系获得
  意义。A1 降格为 L1（VC 维容量引理推出组合必然）; A3 降格为测量约定。
  独立性检验: 冻结压缩器挡"A2⟹A4"，盲选择过程挡"A4⟹A2"，时钟/查找表挡
  "动力学存在性外供"。
- ✅ **选择原理导出已攻克（同日）** (`docs/wiki/selection-principle-derivation.md`):
  三条导出路线全部失败——Landauer 热力学（把物理持存与耦合维持混为一谈,
  岩石零感知也持存）; 无遗憾/通用归纳（条件性成立: 若集合动力学是
  指数加权则收敛到低遗憾结构, 但"动力学是指数加权"本身就是选择原理换了
  精确的衣服——公设被 relocate 而非消灭）; 复制子动力学（fitness=预测效能
  就是公设 II 改名, 只给机制）。**共同撞墙点: 三条路线都预设了要证明的东西
  ⟹ 选择原理是定义性的**——"可观测认知主体" ≡ "输出与世界长期相关" ≡
  "遗憾有界" ≡ "耦合质量优胜者", 这是"主体"一词的分析性内容（如同 F≡ma）。
  移入定义 D4。**公设最终清点: 4 → 2 → 1**（只剩公设 I 压缩 + 存在性陈述）。
  诚实弱点: 只覆盖集合层面过滤器不导出个体规则; 观察者循环性（=自洽方程）;
  bootstrapping（第一个主体起源）超范围。
- ✅ **意外产出 L6 选择算子定律**: 指数加权（选择机制的数学形式）= softmax
  = Gibbs = Boltzmann = 注意力/RLHF 算子的形式。推导路线: 约束最大熵
  ⟹ Gibbs 形式 + Hedge 证明指数加权是 minimax 最优在线规则 ⟹ 同一算子
  既是集合选择机制又是序列注意力算子 ⟹ **自注意力的第一性来源**。
  Lean 内核已在库（`rlhfPolicy`/`softmax_weight_concentration`/`attention_error_bound`）。
- ⏳ **下一轮候选**: ①L6 的完整推导（最大熵+Hedge 组装成定理, 这是"为什么
  注意力有效"的第一性答案）②L2 规模律纸上推导 ③论文 §2-§3 公设章
  （3 定义 + 1 公设 + 失败分析 + L2-L6 清单）
- ⏳ **arXiv:2512.05117 定位调整**: 从主线降级为对照物/交叉验证（其"训练收敛到
  共享低维谱子空间"现象 = A4 动力学的推论形态, 可作 L3 间接经验支持）。
  编译页 `docs/wiki/universal-weight-subspace.md` 已加定位注记; 候选命题 CD1-CD5
  保留（CD1 吸引子存在性 ↔ L3; CD3 有效秩 ↔ L2; CD4 幂律谱层 ↔ L3 临界）
- ⏳ **E8 实验**（scripts/experiments_e8.py 已写好未跑）: 降级为备选交叉验证, 非主线
- ⏳ 公设独立性/极小性待研究: A4 能否从 A1-A3 推出?

## Lean 内核扩充（2026-10-20, 认知动力学两条定律落地）

- ✅ **总计 94 条定理全部机器验证**（`verify_all.sh` ALL-PASS, 0 sorry, 0 warning）:
  原 83 + `Gibbs.lean` 5 + `CognitiveDynamics.lean` 6
- ✅ **`LmPrinciple/Gibbs.lean`（5 定理, L6 选择算子定律的数学核心）**:
  Gibbs 变分原理（有限 Donsker–Varadhan）——`gibbs_variational`:
  E_q[x] − KL(q‖p) ≤ log Σ p·e^x（单步 Jensen + 项级对消, 免微积分）;
  `gibbs_weights_optimal`: **softmax 分配取等**（log q*_i = log p_i + x_i − log Z,
  括号内恒 = log Z）——"率受限下 softmax 是每比特期望分值最大的唯一选择";
  `gibbs_variational_uniform`: 注意力形式 E_q[x] + H(q) ≤ logsumexp(x);
  权重正性/归一性 2 条。推导页 `docs/wiki/L6-selection-operator.md`
- ✅ **`LmPrinciple/CognitiveDynamics.lean`（6 定理, 认知动力学本体层, 并行会话
  初建 + 本会话修复编译）**: `CognitiveSystem` 四层有限结构（世界→感知码→
  内部状态→输出）为本体; T1 无损 ⟺ 承载区分的单射即复合映射; T2 鸽笼基数链;
  T3 感知必单射（压缩只能发生在感知之后——P2 的结构条件）; T4 无损 ⟺
  （感知单射 ∧ 认知⊗表达单射）（感知满射给定）; T5 最优系统
  \|世界\|≤\|感知码\|≤\|输出\|; T6 表达容量 ≤ 内部状态数（自由度载体）
- ⚠️ **本会话对 CognitiveDynamics.lean 的修正**（原文件有 3 处数学/编译错误）:
  ①T1 反向原为假（存在某单射推不出复合映射单射）——改为带等式的正确命题
  ②T4 ← 方向原为假（满射推不出单射）——重述为"感知单射 ∧ 认知⊗表达单射"
  ③Optimal 原定义缺感知单射（T5 第一不等式在旧定义下为假）——增加单射项
  ④v4.35 API 适配: structure 匿名实例字段是语法错误/命名实例字段不被
  inferInstance 采纳 ⟹ 改定理级实例参数; `Nat.card`/`Set.card`/
  `Nat.card_range_le`/`hsur.injective` 在 v4.35 不存在 ⟹ 换
  `Finset.univ.image`+`card_image_le`+`card_univ` 路线
- ✅ **L6 状态**: 半程闭合（Gibbs 变分 = S2 已证; Hedge minimax = S3 文献定理
  待 Lean 化; 完全体 S4 需补 L6-b）
- ⏳ **L6 下一步候选**: L6-b Hedge Lean 化（有限专家集合遗憾界, 潜在函数法）
  / L6-c 唯一性加强 / L3 吸引子与临界（分值构造的第一性）
- ✅ **四组件第一性解释完成** (`docs/wiki/dynamics-source-structure.md`):
  用户概念精确化——**结构是动力学的来源不是舞台**: 研究对象 = 对 (s, 𝒫),
  动力学 = 闭环流 Φ: (s,𝒫)↦(s',𝒫')（智能体作用于世界并收新感知）;
  向量场由结构自身耦合生成, 抽掉结构则"力"不复存在（内生向量场 + 共生态
  空间 + 闭环耦合, 三条一并钉死"动力学≠力学"）。四组件全部挂上定律:
  ①规模法则+截止 = L2 双地板（残余失真 D*(R(N)) + 不可约熵 H(𝒫∣𝒾*), 数据
  地板 T^{-1/2} 来自 UWS Thm 3.7; E7 的 ±0.17 噪声地板是层数维度实证）
  ②反向传播 = **L7**（标量目标 + 巨参数 ⟹ 逆模式 AD 渐近最优, Griewank 界;
  附带解释人脑不反向传播: 选择作用于种群/寿命尺度）
  ③残差 = **L8**（恒等路径 = 流的惯性项/平行移动; 已证 residual_no_collapse
  + FFN 可坍缩; 回答"深层循环为何返回"）
  ④共同基子空间 = L3 经验面孔（吸引子 = 感知流二阶矩主子空间, 由数据统计
  决定; UWS 的"共享基+任务系数"分解 = 协方差 top-k + 特异部分; 模型合并 =
  共享基上凸组合, L6 误差界适用）
- ✅ **"为什么会产生智能"体系内答案**: 智能 = 闭环压缩动力学在选择压下的
  通形——世界可压缩（定义性）+ 率受限耦合（A2）+ 选择过滤（D4）+ 组合容量
  （L1）+ 下降方向（A4）+ softmax 选择（L6）+ 逆模式实现（L7）+ 恒等记忆
  （L8）⟹ 任何持存认知系统必然呈现这些形式
- ✅ **第一轮实验战役完成（E8-E12 全部跑通, 2026-10-20）**
  (`docs/wiki/experiment-results-e8-e12.md`, 脚本 `scripts/experiments_e{8..12}.py`):
  ① **E11 残差消融 = 教科书级确认 L8**: 无跳连分离度 0.637→0.610→**0.000→0.000**
  （深度 6 起完全坍缩）; plain 0.636→0.642→0.632→0.633（跨深度恒定）;
  gated 恒定且 loss 斜率最优（+0.0067/层）② **E12 逆模式 vs 无梯度 = 12.5×**:
  Adam 降 4.93 vs ES 降 0.61 vs 爬山降 0.07（同 20s 预算, 每前向当量）,
  支持 L7 且差距是下界（极小模型上 ES 本应有竞争力）③ **E8-8A 普适性本地复现**:
  域内 0.684 vs 域间 0.797, **比值 1.17**; k=1 占 36.8% 方差; 8C
  Spearman(β,Δ_k)=+0.370 支持"幂律谱层更可训练"④ **E9 规模双区间**:
  T=10K 时参数越多越差（4.27→5.42, 数据受限区）; T=160K 时 dim48→96 只降
  0.016（参数受限区）; 幂律斜率 −1.2/−3.2; **可加性失败 ⟹ L2 陈述修正为
  "N/T 配比决定绑定约束"的区间形式**（实验纠正理论的第一个闭环）⑤ **E10 退火
  部分支持**: Spearman(深度,β_eff)=+0.566, 首层明确探索（β_eff 最低+熵最高）,
  跨深度单调退火未获支持⑥ **E8-8B 负面（设计受限）**: rank-2 子空间被 seed 噪声
  主导, T^{-1/2} 本地检验失败, 列 E8-b（需同 seed 跨数据或更多模型）
- ⏳ **下一轮实验候选**: E13-b（R(N,T) 二变量封闭式 + 第二语料族验 γ(T) 普适性）/
  E13-c（test−train 拆成容量不足 vs T^{-1/2} 估计误差, 即 E8-b 的正确设计）/ E8-b（T^{-1/2} 的正确设计: 同 seed 跨数据子空间对比）/
  E10-b（训练更好的深网测退火: 余弦 lr + 更长训练）/ E9-b（更大网格确认
  双区间边界）
- ✅ **公设升级 + 五组件推导完成** (`docs/wiki/component-derivations.md`):
  用户指认"压缩只是数据压缩, 残差/注意力/规模还没解释" ⟹ 公设 I 升级为
  **双轴率受限 I'**: 轴 1 静态表征率（词元/维度）+ 轴 2 动态计算率（顺序
  操作/时间/数据搬运）; 原单轴版只是轴 1 特例; **五组件全是轴 2 的最优解**。
  ①自注意力 = 轴 2 全局路由（路径长度 O(1) vs O(n) 复杂度账本 + 条件集越大
  失真越低的单调性; 形式由 L6 定、范围由本推导定; 接 Bahdanau/Transformer
  论证从经验升格为公设后果）②残差 = 迭代压缩的参照系 = 相图临界线
  （1908.10920 的 χ_q*,χ_c*: χ<1 有序饱和/χ>1 混沌爆炸/χ=1 临界可任意深度
  传播; 残差把 Jacobian 谱手术刀式钉在 ≈1, 把"临界线初始化的幸运"变成架构
  保证; "深层循环为何返回" = 平行移动的参照系需要）③规模 = 候选扩展受有效秩
  封顶（N↑⟹候选↑⟹失真↓; 封顶在数据谱有效秩, UWS 19×/100× 的直接证据;
  人脑对比 = 静态效率 vs 元压缩/适应两种优化目标）④log/非线性/概率 Q&A:
  非线性最简描述 = Lyapunov 谱（复利=指数映射; log 域操作）; 概率两来源 =
  部分可观测边际化 + 正 Lyapunov 确定性动力学的 SRB 唯一统计描述
  （"动力学产生概率"的严格版）; 相图三态 = 可压缩性三态（可学习 = 骑临界线,
  E8-8C +0.370 与此接龙）⑤FEP 三缺口全部回答（规模=容量-谱尾权衡/连续关系=
  参照系需要/循环=同一失真泛函的迭代松弛且稳定性由 Lyapunov 谱判定）
- ⏳ **组件推导的待证项**: 注意力全局性的有限假说类形式化（条件集-失真
  单调性）/ 残差 Jacobian 谱半径 ≤1+ε 的严格证明（线性代数, 可做）/ 规模
  "半推导"补全（容量+UWS 的组装定理）
- ✅ **预测差距诚实账簿** (`docs/wiki/predictive-gap.md`): 用户问"是否算出了
  所有大模型的困惑"——**答案: 没有**。已证: provable 双重界限（CE≥数据熵
  下界 + 2^R 容量上界, 任何模型任何数据）; 未证: 先验数值预测（牛顿标准的
  核心）。三个关键缺口: ①感知流谱 {λ_i} 的先验测定（从未从数据测量谱再
  预测损失）②架构→可达率 R(N) 的封闭映射 ③优化缺口（零理论）。
  正确定位 = **开普勒阶段**: 有经验律 + 若干定理, 无预测公式。
  **E13 分水岭实验已设计**: 测数据谱（SVD）+ xz 熵地板 + 组装
  L̂(N,T) = H_floor(T) + C·I(N)^{-β}（I=交互计数, Efficiency.lean 公式）,
  预测 E9 网格 9 点对照实测——从"训练后测量"走向"先验计算后对照"。
- ✅ **E13 已执行（2026-10-21, 远程 2×A100-40GB, 36 次训练）** (`docs/wiki/experiment-results-e13.md`,
  脚本 `scripts/experiments_e13.py`): **先验预测未过判据** —— 预测在任何训练前写盘
  (sha256 2e837863d6a34d0a), 12 格（dim{24,48,96,192} × T{10K,40K,160K} × 3 seeds）
  对照 **MAE 0.472 nats** vs 训练噪声 0.019。三条定量产出:
  ① 误差**符号随 T 翻转**（−0.877 / −0.305 / +0.146）⟹ 公式缺 T 项;
  ② 反演所需率 R_eff 在每 T 内是干净幂律（R²=0.97）但**指数 γ 依赖 T**（0.067/0.121/0.166）,
  且计数型先验 R(N)=ln(Nn²/3d²) 几乎不随 N 变（12.48→11.68, N 变 29×）⟹ **缺口 #2 是 R(N,T)**;
  ③ dim192/T160K 训练损失 1.556 **低于 xz 地板 1.628** ⟹ **优化缺口 ≈0**, 绑定项是
  test−train ≈1.1–1.3 nats 的泛化/估计。谱侧先验量可测: α≈2.0–2.4（在 UWS α∈[2,6] 内）,
  有效秩 20→40, I(ctx;next) 2.95→3.57 nats; 地板必须用**条件压缩率**（单段 xz 小窗虚高 0.6–1.4）。
  协议变更: 块级随机 80/10/10 + val 最优 checkpoint（E9 的尾部 64 字符单窗噪声地板达 0.45 nats）;
  架构改 pre-LN（post-LN 3000 步 lr=3e-3 发散）⟹ 与 E9 的 2.61 不可直接比数。
- ✅ **GPU 放大批次完成（2026-10-21, 远程 2×A100-40GB, vllm-cu128/torch2.9.1+cu128）**
  (`docs/wiki/experiment-results-gpu.md`, 脚本 `scripts/gpu_experiments.py` CUDA 感知):
  把 CPU 冒烟版 E8–E12 搬上 GPU 放大 + 新增 E13 先验预测（率失真注水, 复用 gpu_e9 网格,
  与旧公式版 experiments_e13.py 不同: 该版 MAE 0.472 未过, 本版 MAE 2.80 不成立但反演定位到缺口 #2）。
  结论**复现并多处加强** CPU 冒烟版: ①**E11 残差 = L8 强支持**（无跳连深度4起 sep 全坍缩为0,
  plain/gated 跨深度恒定 ~0.44; GPU 比 CPU 更早更强）②**E12 逆模式 = L7 方向支持**
  （同预算同初始化 Adam 每前向 2.8×/5.0× 优于 ES/爬山, 修正首版 ES 发散）③**E9 规模 =
  双区间 + Chinchilla 式 crossover 起点**（T=100-200K 越大越差; T=300K 时 dim512(3.723)
  首次<dim256(3.734); 幂律-over-N 因最大模型非地板而不可定义）④**E8-8A 普适性弱复现**
  （域间/域内=1.27）+ **8C Spearman(β,Δ_k)=+0.461**（CPU+0.370 更强）+ **8B T^{-1/2}
  确认是边界**（同 seed 跨数据 K=5 正确设计下仍平坦, 斜率0.018）⑤**E13 先验预测 =
  做了**: 谱给预算给不到损失地形——公式 R_cap 注水 **MAE 2.80 nats 不成立**（率尺度错配,
  过度注水）; 反演 `R_needed` 得 **∝lnT +0.83 / ∝lnN −0.46** ⟹ **可达率由数据 T 门控**,
  精准定位**缺口 #2（架构→可达率 R(N,T) 未闭合）**; 同时先验测出 **H_floor=0.931 nats/char**、
  **E9 最小实测 2.483 ⟹ 预测缺口 1.553 nats**（= 未闭合 R(N,T) 缺口的实测总和; 直接回答
  "是否算出所有困惑": 没算数值但测到下界并量化了差距）。
  诚实边界: 单语料族/3seeds/弱训练验证性实验; E9 卡数据受限区故 β-fit 不可定义;
  E8-8B 是真边界; E13 地板与 E9 来自不同语料快照(近似对照); E13 先验预测作为点预测不成立,
  但把缺口 #2 从假设提升为实测确认的边界。
  ✅ **L-data 攻下 + E13-cross 确认数据门控方向（2026-10-22）**: `LmPrinciple/DataRate.lean`
  Lean 证 `data_rate_mono`（数据率随 T 单调不减, 无 sorry）; GPU 细 T 网格反演
  `R_needed∝lnT +0.527 / ∝lnN −0.431`——与 Lean 方向**一致**（数据门控）; MAE 3.38 仍失败
  （缺口#2 整体未闭合）。**语料天花板 ~849K**: crossover/参数受限实验需 >2M 语料, 暂被数据卡死。
  ✅ **B 冻结语料复核 + C 的 L-eta 方向内核（2026-10-22）**: B 加 `freeze` 冻结语料重跑,
  **查明此前"语料快照不同步"是误读**（run_e13 的"848730"是 `" ".join` 空格连接字节≈2×; e9/e13 一直是同一 ~354K 语料, 冻结后输出不变）; lnT 幅度差异是**网格 T 范围**不同（旧+0.83/新+0.53）非语料。  C 的 L-eta: `LmPrinciple/OptEff.lean` Lean 证 `loss_mono_in_eta`
  （损失随优化效率 η 单调不增, 无 sorry）; η 的具体值/上界（优化缺口③）仍开放。
  ✅ **η 的"毛球折叠"几何重构已形式化（2026-10-22, 接用户直觉）** `LmPrinciple/Folding.lean`:
  η=折叠深度（表示流形往低失真/吸引子折叠的程度）; `loss_after_fold_mono`（折越深损失越低）+
  `full_fold_reaches_floor`（η=1 折到底⟹损失=地板, 对应实测记忆化）+ `capped_fold_above_floor`（封顶⟹下不去）;
  HB1 桥接 `forced_zero_trapped`/`residual_removes_forced_zero`（标量 η↔拓扑零点是建模桥）。验证留后（折叠深度实测标定）。
- ✅ **拓扑构造实验完成（2026-10-22, 本地 CPU 秒级, `scripts/topo_experiments.py`）**
  (`docs/wiki/topology-hairyball-notes.md`): 用户新方向——"智能=结构/动力学而非数学描述",
  落到毛球定理与兰顿蚂蚁。①**E-TOPO-1 兰顿蚂蚁**：11000 步无损失/无优化器，~10k 步后突现
  周期 104 步的 highway 吸引子（规则即梯度、吸引子定轨迹）→ 演示 **A4 内生动力学**；
  ②**E-TOPO-2 毛球定理**：S² 上切向量场解析零点=2（Poincaré-Hopf χ=2），严格切向动力学
  1674 步内被吸向极点卡死（场范数≈1e-8=坍缩=那个"坑"），加一条法向"残差"路径后轨迹
  越过极点离面（半径1.45）未坍缩 → **毛球定理给 L8 残差一个拓扑根**（候选定理 HB1）。
  诚实分层：毛球→L8 是真拓扑必然（强启发+候选定理）；兰顿蚂蚁是说明性载体（非证据）；
  π/表面积是非线性类比（未入公式）；手性首次产生=开放问题。
  ③**HB1 初等内核已 Lean 机器验证**（`LmPrinciple/HairyBall.lean`, 无 sorry/axiom,
  `#print axioms` 仅 `[propext, Classical.choice, Quot.sound]`）: `forced_zero_trapped`
  （两端向内的连续下降流必有零点=被闭域困住则坍缩拓扑强制）+ `residual_removes_forced_zero`
  （残差越界后存在无零点下降流=残差打破强制停滞）+ `s1_tangent_nonvanishing`（S¹ 奇维可梳，
  反衬障碍维度奇偶特异）。完整毛球定理（偶维球面无无处非零切场）需 degree 理论, 记为形式化目标。

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

1. **工具链**: `lean-toolchain` 固定 `leanprover/lean4:v4.35.0`（elan 已装；当前机已装 v4.35.0）
2. **mathlib**: 当前工作机（macOS）`.lake/packages/mathlib` 为指向
   `../NavierStokesAndEuler/.lake/packages/mathlib` 的符号链接，已 checkout **tag
   v4.35.0 提交 56a0058**（2026-10-13）。⚠️ 该 tag 可能已被移动：若重新物化，须用
   `git log --lean-toolchain` 找到原始提交，取其**自己的** manifest 里的 dep rev
   （全 4.35 时代，lean-toolchain 均 = v4.35.0）
3. **8 个依赖**（batteries/Qq/aesop/proofwidgets/importGraph/LeanSearchClient/
   plausible/Cli）: 同样以符号链接复用 NavierStokesAndEuler 的依赖集，checkout
   mathlib@56a0058 manifest 里的精确 rev（全 4.35 时代，lean-toolchain 均 = v4.35.0）
4. **lakefile.toml**: mathlib + 8 依赖全部 `path` require → 解析完全离线，
   不需要 manifest / 网络 / Reservoir
5. **构建**: 用**真实 lake 二进制**（elan shim 启动即解析默认工具链 v4.33.0 未装
   → 尝试下载 → 假失败）: `~/.elan/toolchains/leanprover--lean4---v4.35.0/bin/lake
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

## 环境坑（历史 Windows + 当前 macOS）

- curl schannel 吊销检查失败（CRYPT_E_REVOCATION_OFFLINE）：lake 进程内 libcurl
  无法关闭 → 只能 git（SSH）物化 mathlib
- raw.githubusercontent.com / github.com 间歇不可达（无代理），SSH 协议可用
- 后台命令 UTF-16 BOM 污染 → 长命令写 .sh 脚本再执行
- lean-toolchain 别改回 v4.34.0-rc1 或其他旧版（Batteries 语法不兼容，会编译失败）；
  当前固定 v4.35.0；`scripts/setup_mathlib.sh` 是 Windows 专用
- Lean 4.21 core 只有 omega；linarith/nlinarith/ring/field_simp 需
  `import Mathlib.Tactic.{Linarith, Ring, FieldSimp}`
- importGraph 仓库名带连字符 `import-graph`（≠ importGraph），克隆前先查 manifest
- `∑ x in s` 记法在 v4.35 **已被移除**（硬语法错误 `unexpected token 'in'`）→ 必须用 `∑ x ∈ s`
- elan shim（~/.elan/bin/lake）默认工具链解析可能未装 → 假失败，
  一律用 `~/.elan/toolchains/leanprover--lean4---v4.35.0/bin/lake`（真实二进制）

## 相关文档

- 来源: LMT-twister 论文 head-en.tex / head-zh.tex（附录 A 引理 A.1-A.4）
- 架构: `docs/wiki/project-overview.md`
- 日志: `docs/wiki/log.md`
