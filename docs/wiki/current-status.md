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
