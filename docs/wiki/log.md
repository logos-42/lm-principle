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
| 2026-10-22 | 认知动力学 | L-data 攻下 + GPU E13-cross 确认数据门控方向 | **用户"攻 L-data, 攻完炮 GPU 实验, 守着进度自动接, 要预测"**。①**L-data Lean 证** `LmPrinciple/DataRate.lean`: `data_rate_mono`(UWS T^{-1/2} 地板为假设, R_data(T)=Σ max(λ_i−εT)0 随 T 单调不减)+`usable_modes_mono`, 无 sorry。②**A100 隧道曾失效**(6100 端口开但无 SSH banner, 上个 session 转发过期), 用户重连后恢复 2×A100-40GB。③**GPU E13-cross**(细 T 网格 dims{128,256,512}×T{50K,100K,200K,353K}×3 seeds, GPU0, 守着跑完自动接 e13): 反演 `R_needed∝lnT +0.527`(>0 数据门控)/`∝lnN −0.431`(<0 越大越差)——与 Lean `data_rate_mono` 方向**一致**; 点预测 MAE 3.38 仍失败(缺口#2 未闭合); H_floor 0.931/D0 3.688/gap 1.316。**发现语料天花板**: 清洗后~849K 字符, T=400K 被截到 353K ⟹ 参数受限区 crossover 实验被数据卡死(需 >2M 语料), 本次只在数据受限区内校准 L-data。诚实: lnT 幅度随语料快照浮动(旧+0.83/新+0.53; e9 训练~353K vs e13 反演~849K 不同步, 中途加 wiki 页)。结果存 gpu_e9.json/gpu_e13.json; gap2 目标书回写 |
| 2026-10-21 | 认知动力学 | E13 先验预测（GPU 批次, 率失真注水复用 gpu_e9 网格） | **用户"做一下 E13 先验预测"**——把之前只做了熵地板/缺口的部分补成真正的先验预测。方法: 语料转移矩阵 SVD 取谱 λ, D0=单字CE−H_floor(3.688), 用 Efficiency.lean 交互率 R_cap(N) 注水预测 E9 网格 9 点 loss (实测真值, 同族已训), 并反演 R_needed 检验可达率门控。结果: **公式点预测不成立 MAE=2.80 nats**(R_cap 率尺度错配, 过度注水, 预测值系统性远低于实测); 但反演得 **R_needed ∝ lnT +0.83 / ∝ lnN −0.46**(R_cap↔R_needed 相关+0.69) ⟹ **可达率由数据 T 门控而非容量 N**——精确确认 `predictive-gap.md` 的**缺口 #2 (架构→可达率 R(N,T)) 未闭合**。同时先验测出 H_floor=0.931 nats、E9 最小实测 2.483 ⟹ 预测缺口 1.553 nats (= 未闭合 R(N,T) 缺口的实测总和)。结论从"假设缺口 #2"提升为"实测确认的边界"。脚本 `scripts/gpu_experiments.py` run_e13 已重写; 汇总见 `experiment-results-gpu.md` §5; current-status/index 同步 |
| 2026-10-22 | 认知动力学 | 缺口 #2 推导目标书 R(N,T)（C→B→A 之 C 第一步） | **用户定优先级 C→B→A 并选"先 1 后 3"**——HB1 Lean 已完成(选项1)；现做选项3: 把缺口 #2 从"假设"升级为可施工推导目标。新建 `docs/wiki/gap2-rnt-derivation.md`: 目标定理 **G2** = `R_ach(N,T,{λ}) = min(R_cap(N), R_data(T)) · η(N,T)`, 使 `L̂ = H_floor + waterfill_D(λ, R_ach)`; 三条 E13 反演经验约束 (R_needed∝lnT +0.83 主导 / ∝lnN −0.46 / R_cap↔R_needed +0.69, 数据受限区数据门控); 三个缺失引理 **L-data**(数据率 c(λ)·lnT, 接 UWS T^{-1/2}) / **L-eta**(优化效率, 缺口③最弱) / **L-switch**(crossover N*(T)=Chinchilla 最优配比); Lean 钩子 (Efficiency.interaction_rate / Training.scaling_law_strict_anti / Fractal 幂律) 与需新增三条引理; 可证伪预测 (crossover 位置 / 参数受限区 β-fit 恢复 / E13-b 第二语料族)。诚实边界: min·η 结构是假设形态, E13 只支持"数据门控"这一半。index/predictive-gap 挂链 |
| 2026-10-22 | 认知动力学 | 拓扑构造实验 E-TOPO-1/2（毛球定理 + 兰顿蚂蚁, 本地 CPU） | **用户新方向: 智能=结构/动力学而非数学描述**, 落到毛球定理与兰顿蚂蚁, 并要求"主动构造这种拓扑结构"。读 `universal-weight-subspace.md`(吸引子/普适子空间) + `paper-llm-fractal-criticality.md`(规模律几何必然) + `dynamics-source-structure.md`(A4 内生向量场), 写笔记 `topology-hairyball-notes.md` 忠实记录直觉并分层"严格数学 vs 类比"。新建 `scripts/topo_experiments.py`: **E-TOPO-1 兰顿蚂蚁**——11000 步无损失/无优化器, ~10k 步后突现周期 104 步 highway 吸引子(位移(−1,−2)) → 演示 **A4 内生动力学**(规则即梯度、吸引子定轨迹); **E-TOPO-2 毛球定理**——S² 切向量场解析零点=2(Poincaré-Hopf χ=2), 严格切向动力学 1674 步内被吸向极点卡死(场范数≈1e-8=坍缩=那个"坑"), 加一条法向"残差"路径后轨迹越过极点离面(半径1.45)未坍缩 → **毛球定理给 L8 残差一个拓扑根(候选定理 HB1)**。诚实分层: 毛球→L8 是真拓扑必然(强启发+候选定理); 兰顿蚂蚁是说明性载体(非证据); π/表面积是非线性类比(未入公式); 手性首次产生=开放问题。**HB1 初等内核已 Lean 机器验证**: `LmPrinciple/HairyBall.lean`（无 sorry/axiom, `#print axioms` 仅 `[propext, Classical.choice, Quot.sound]`）——`forced_zero_trapped`(两端向内连续下降流必有零点=被闭域困住则坍缩拓扑强制)+`residual_removes_forced_zero`(残差越界后存在无零点下降流=残差打破强制停滞)+`s1_tangent_nonvanishing`(S¹ 奇维可梳反衬障碍维度奇偶特异); 完整毛球定理(偶维球面无无处非零切场)需 degree 理论, 记为形式化目标。index/current-status 同步 |
| 2026-10-21 | 认知动力学 | GPU 放大批次 E8-E12 + E13 熵地板（A100/vllm-cu128） | **用户"全部都试试"在 GPU 上跑**——把 CPU 冒烟版 E8–E12 搬上 2×A100-40GB（vllm-cu128, torch2.9.1+cu128）放大 + 新增 E13 熵地板实测（与公式版 E13 不同）。整合脚本 `scripts/gpu_experiments.py`（CUDA 感知, 子命令 e9/e11/e12/e8/e13, CLI 可覆盖 dims/Ts/steps/seeds/lr/budget）。结论**复现并多处加强** CPU: ①**E11 残差=L8 强支持**——无跳连深度4起 sep 全坍缩为0（CPU 深度6）, plain/gated 跨深度恒定~0.44 ②**E12 逆模式=L7 方向支持**——同预算同初始化 Adam 每前向 2.8×/5.0× 优于 ES/爬山（修正首版 ES 发散: 固定评估 batch+K=32+更小 sigma）③**E9 规模=双区间+Chinchilla 式 crossover 起点**——T=100-200K 越大越差(5.65 vs 4.13@100K), T=300K 时 dim512(3.723) 首次<dim256(3.734); 幂律-over-N 因最大模型非地板而不可定义 ④**E8-8A 普适性弱复现**(域间/域内=1.27)+**8C Spearman(β,Δ_k)=+0.461**(CPU+0.370 更强)+**8B T^{-1/2} 确认是边界**(同 seed 跨数据 K=5 正确设计下仍平坦, 斜率0.018, 非设计缺陷) ⑤**E13 熵地板实测=0.927 nats/char**(xz 压缩率, 不可约下界)+**E9 最小实测 2.483⟹预测缺口 1.556 nats**(容量+优化+估计三混合, 理论未拆分; 直接回答"是否算出所有困惑": 没算数值但测到下界)。诚实边界: 单语料族/3seeds/弱训练验证性; E9 卡数据受限区故 β-fit 不可定义; E8-8B 真边界; E13 地板与 E9 来自不同语料快照(近似对照)。汇总页 `docs/wiki/experiment-results-gpu.md`; current-status/index 同步 |
| 2026-10-21 | 认知动力学 | E13 先验预测首次执行（远程 2×A100）：未过判据，失败定位到 R(N,T) | **在服务器（ssh -p 6100, /work/liuyuanjie/lm-principle）用 2×A100-40GB 跑完 36 次训练**。①**协议**（必须先说，否则数不可比）: 预测在任何训练前写盘（`e13_predictions_full.json`, sha256 2e837863d6a34d0a, mtime 04:02 vs 实测 04:15）; 链 = 条件 LZMA 地板 H_floor(T) + 测得谱上的逆向注水失真 D(R(N))，R(N)=ln(N·n²/3d²)（Efficiency.lean 交互率），**零个从 loss 拟合的参数**; 网格 dim{24,48,96,192}×T{10K,40K,160K}×3 seeds; 块级（256 字符）随机 80/10/10 + val 最优 checkpoint（尾部单窗协议下同模型 val 5.42 vs test 4.97，文件异质性噪声 0.45 nats > 待检验效应）; 架构改 pre-LN + 末端 LN（E9 的 post-LN 在 3000 步 lr=3e-3 下**发散**，test 14.5）⟹ **与 E9 的 2.61 不可对号**。②**判定: 未通过**——MAE **0.472 nats** vs 训练噪声 **0.019**（判据 <±0.2）。但 12 格误差**符号随 T 翻转**: T=10K −0.877 / 40K −0.305 / 160K **+0.146** ⟹ 不是系数问题，是**公式缺 T 项**。③**缺口 #2 改写为 R(N,T)**: 反演（实测超额在测得谱上反解所需率）得 R_eff 在每个 T 内是干净幂律（R²=0.966/0.974），但**指数 γ 依赖 T**: 0.067→0.121→0.166; 而先验 R(N) 几乎不随 N 变（12.48→11.68，N 变 29×，因 N∝d² ⟹ ln(N/d²)≈常数）——**计数型容量界在结构上产生不出观测到的 N 斜率**; R_eff 随 T 穿过先验值（10K: 4.9–6.7 ≪ 12.5; 160K: 10.3–18.1 > 12.5）就是误差符号翻转的机制。留出检验（dim24/48 拟合 a,γ → 预测 96/192）平均 |误差| 0.339，**幂律形式可迁移、系数不可迁移**。④**缺口 #3 被量到 ≈0**: dim192/T160K 训练损失 **1.556 已低于 xz 地板 1.628**（记忆化）⟹ 优化缺口（SGD 未到最小）非绑定项，绑定项是 **test−train ≈1.1–1.3 nats 的泛化/估计**；缺口 #3 从「零理论」变「可分离且主项不在优化」。⑤**先验量可测**: 谱指数 α≈2.0–2.4（落在 UWS suitability α∈[2,6]）、有效秩 20→40（**不封顶在 16**，与 UWS「≤16 维跨任务共享子空间」不是同一个量）、I(ctx;next) 2.95→3.57 nats; 地板**必须用条件压缩率**（[xz(train+test)−xz(train)]/len(test)），单段 xz 在小窗虚高 0.6–1.4 nats。⑥**工程坑**: post-LN + lr 3e-3 + 3000 步 = 发散（loss 14.5）; 固定步数同时测到欠拟合与过拟合（最优步 100–2967）⟹ 必须 val 最优 checkpoint + patience; `R_of_D` 初版因取 log(λ/1e-12) 得负数上界而返回垃圾（−11481），修正为按 λ_max·1e-12 截断。新建 `docs/wiki/experiment-results-e13.md`（含全部表）; predictive-gap.md 缺口 1/2/3 状态与时间线回填; current-status/index 同步; 下一轮: E13-b（R(N,T) 封闭式 + 第二语料族）/ E13-c（容量 vs T^{-1/2} 分解） |
| 2026-10-20 | 认知动力学 | 框架定位: 与八家的绝对差别 + 为何只解释一部分 + 数学成立四层回答 | **用户三问**: 绝对差别在哪/为何只解释一部分/数学模型为何成立。新建 `docs/wiki/framework-positioning.md`: ①一句话差别: 别人把智能组件当给定描述其行为, 我们把一条经验前提（感知=双轴率受限压缩）当给定推导组件必然形式——**他们的研究对象是神经网络, 我们的是"率受限压缩机"（DNN/脑/外星智能都是实例非主题）**。三条绝对差别: 解释方向相反（系统→数学 vs 公设→数学→系统, 牛顿方向）; 经验前提数目（他们复数隐含, 我们 1 公设+3 定义+1 存在性陈述且证明过半是定义性的）; 闭环内生动力学（无外部优化器/生态位, 向量场由结构-感知耦合自生, 选择是定义性的, 下降方向是推出来的）。②八家对照表（1908.10920: 他们解释传播我们解释架构, L8 把临界线从幸运变必然; Tishby: 压缩当描述 vs 当本体论, 我们多一个计算轴; FEP: 最近亲戚, VFE 贝叶斯构造 vs 失真信息论构造, 他们无显式率限公设故推不出架构与规模, 其"持存者持存"正是我们证明为定义性的一环; 优化/SLT/规模实证/UWS/Landauer 各就各位, Landauer 导出失败存档）。③为何只解释一部分: **必要条件理论非充分条件理论**——公设筛掉不可能形式但不唯一确定充分形式; 解释不变量（跨系统共性, 第一性本义）不解释变体（具体子空间/损失值/轨迹, 由数据谱训练史实现决定）; 数学上算优化问题的形式与界不算具体实例的解（变分原理告诉你光走极值不告诉你今天照哪面墙）。④数学为何成立四层: 可压缩性前提（数学成立因世界有可压缩结构; 循环性诚实承认: "数学为何成立"="世界为何可压缩", 是地基经验事实只能测量——E13 正是测它）; 选择效应（Wigner 之问的回答: 数学对我们研究的那部分现实有效, 而那部分被选择出来——只有稳定可压缩的结构才进入任何理论视野, 我们研究持存者, 持存者最 lawlike）; 定理链必然性（遗憾界=可计算性定理/Gibbs=凸性定理 Lean 已证/防坍缩=压缩映射定理/2^k=组合定理; 数学成立方式与牛顿同: 定义+最少经验前提+定理, 我们优势是前提最少显式故边界最清晰）; 适用边界（世界不可压缩/率限不绑定/闭环断裂/选择不起作用——四个必须失效的场景, 知道在哪失败是可被信任的前提）。⑤诚实清单: 无优化理论无泛化界无大规模验证, 谱机器全是引用, L2/L3/L7 半推导, E13 未做——优势在本体论极小性+推导方向+闭环内生（范式级）, 劣势在成熟度（工作量级） |
| 2026-10-20 | 认知动力学 | 预测差距诚实账簿: 牛顿标准对照 + E13 分水岭设计 | **用户之问: "我们是否计算出了所有大模型的困惑?"——答案: 没有**。新建 `docs/wiki/predictive-gap.md` 记账: ①牛顿标准 = 先验算出任意 (架构,N,数据) 的困惑度无需训练; 现状: 能算 **provable 界限**不能算**数值**。②已证（Lean 94 定理中的相关群）: CE≥数据熵（任何模型任何数据的困惑度绝对下界, InfoDynamics）+ 2^R 容量计数（上界锚定, LMT）+ 每参数交互率 n²/(3d²)（架构轴 2 容量, Efficiency）+ 组合容量 2^k（CognitiveDynamics）+ L=c/(N+1)^α 递减形状（Training）+ L4 最优深度 + L6 softmax（半程）。③未证三缺口: 感知流谱 {λ_i} 的先验测定（从未从数据测谱再预测损失）/ 架构→可达率 R(N) 封闭映射 / 优化缺口（零理论, Lyapunov 是候选入口未接上）。④缺口定位: E9 实测 2.61 nats vs 熵地板 ~1.5 nats（LZMA 可测）, 差 = 容量不足+优化缺口+估计误差三项混合, 目前一项都不能单独算。⑤正确定位 = **开普勒阶段**: 有经验律（规模律/普适性/坍缩相变）+ 若干定理, 无预测公式。⑥**E13 分水岭实验设计**: 测数据谱（上下文→下一字符统计矩阵 SVD, E8 机器直接用）+ xz 压缩率测熵地板 + 组装 L̂(N,T) = H_floor(T) + C·I(N)^{-β}（I=交互计数, C/β 只从谱拟合不碰 loss 数据）⟹ 预测 E9 网格 9 点对照实测; 判定: 误差 < 训练噪声 ±0.2 nats ⟹ 第一个先验预测成立。E8-E12 全是"训练后测量"（现象学）, E13 是"先验计算后对照"（预测性）——后者才是牛顿标准的检验。时间线: 界限✅ / E13 可立即做（CPU 数小时）/ 跨架构通用公式需 R(N) 封闭映射（周级）/ 优化缺口（月级开放问题） |
| 2026-10-20 | 存档 | push 3cbc84a: 认知动力学立项全套 | **已推送** commit 3cbc84a（7356de5..3cbc84a, master）: 认知动力学立项全部工作——公设体系 5 页 + Lean 94 定理（Gibbs 5 + CognitiveDynamics 6）+ E8-E12 实验脚本与结果 + 组件推导 + raw manifest 登记 + verify_all.sh 门禁更新。27 files, +3162 行。推送前手动跑门禁（lefthook 未装钩子到本 repo）: verify_all.sh ALL-PASS + wiki_lint 19 页 OK |
| 2026-10-20 | 认知动力学 | 公设升级双轴 + 五组件推导: 注意力=全局路由/残差=临界线/规模=候选扩展 + FEP 三缺口回答 | **用户指认**: "我们的压缩只是对于数据的压缩, 残差连接、自注意机制以及规模法则还没有进行解释。我之前给你的论文里是有说的"（重贴三原理+弱点+时钟类比+log/非线性/概率+FEP 三缺口+注意力/规模/人脑论点）。**核心动作**: 公设 I 升级为 **I' 双轴率受限**——轴 1 静态表征率（词元/维度, 原公设只是此轴特例）+ 轴 2 动态计算率（顺序操作/时间/数据搬运, FlashAttention 同数学不同 IO 不同算力 = 轴 2 的物理证据）; **五组件全是轴 2 的最优解**。新建 `docs/wiki/component-derivations.md`: ①**自注意力 = 轴 2 全局路由**: Transformer 论文的复杂度账本（自注意力 O(1) 顺序操作 vs 循环 O(n), 最大路径长度 O(1) vs O(n)）+ 条件集越大可达失真越低的单调性 ⟹ 注意力是单位计算内条件集最大的结构; 与 L6 分工: L6 定选择算子的**形式**（softmax）, 本推导定**范围**（全局）; 用户原话"全局关联性→更多可能性选择→叠加范围更大"= 轴 2 最优的直觉版。②**残差 = 迭代压缩的参照系 = 相图临界线**: 深度 = 轴 2 时间展开的迭代细化; 细化需要跨层可比 ⟹ 共同参照系 ⟹ 恒等路径（"深层循环为何返回" = 平行移动, 非回声）; 1908.10920 的 χ_q*,χ_c* 相图（χ<1 有序饱和/χ>1 混沌爆炸/χ=1 临界任意深度传播）⟹ 残差把 Jacobian 谱钉在 ≈1, 把"沿临界线初始化的幸运"变成架构保证。③**规模 = 候选扩展受有效秩封顶**: N↑⟹2^k 容量↑⟹候选↑⟹失真↓; 封顶在数据谱有效秩（L3 吸引子, UWS 19×/100× 证据）; 人脑对比精确化为两种优化目标: LLM 静态压缩效率 vs 脑元压缩/适应（重塑压缩器本身）⟹ "参数不是越大越好, 适应性越强越好"有了框架内表述, 并接"无形的随时在线"路线。④**log/非线性/概率 Q&A**: 非线性最简描述 = Lyapunov 谱（\|q_t−q*\|~e^{−t/ξ}, χ=e^{−1/ξ}; 复利=指数映射=Lyapunov 指数; 操作全在 log 域）; 概率两来源均非根本随机: 部分可观测的边际化 + 正 Lyapunov 确定性动力学的 SRB 唯一统计描述（"动力学产生概率"严格版）; 相图三态 = 可压缩性三态, 可学习 = 骑临界线（与 E8-8C +0.370 及 suitability α∈[2,6] 接龙）。⑤**FEP 三缺口全答**: 更多神经元→更小 VFE = 容量-谱尾权衡（L1+L2）; 连续关系/循环返回 = 参照系需要（残差推导+L8 已证）; 循环 = 同一失真泛函的迭代松弛（A4 离散形式）, 稳定性由 Lyapunov 谱判定。框架页公设同步升级为 I', 定律表加组件映射指针, 索引/current-status 回写。诚实边界: 注意力全局性是复杂度-失真论证非定理; 残差-临界线是解释性等同（严格版待 Jacobian 谱半径证明）; 规模是半推导; SRB 为引用。**待证项**: 注意力条件集-失真单调性的有限形式化 / 残差 Jacobian 谱半径 ≤1+ε / 规模组装定理 |
| 2026-10-20 | 认知动力学 | 第一轮实验战役 E8-E12 全部完成: L8/L7 强支持, L2 被修正为双区间, L3 普适性复现 | **用户指示"全部都完成"——五个实验全部跑通**（脚本 `scripts/experiments_e{8..12}.py`, 数据 `experiments/results/e*.json`, 汇总页 `docs/wiki/experiment-results-e8-e12.md`）。①**E11 残差消融 = 教科书级确认 L8**: 无跳连分离度 0.637(L2)→0.610(L4)→**0.000(L6)→0.000(L8)** 深度 6 起完全坍缩; plain 恒等 0.636→0.642→0.632→0.633 跨深度数值恒定; gated 恒定且 loss 斜率最优(+0.0067/层 vs plain +0.016 vs none +0.267)——`residual_no_collapse` 的实验面孔, 相变式坍缩。②**E12 逆模式 vs 无梯度 = 12.5×**: 同 20s 同初始化 (N=79,963): Adam 7.4153→2.4862 (降 4.93, 897 前向当量) vs ES(K=16) 降 0.61 (1424 前向) vs 爬山降 0.07 (1376 前向); 每前向当量效率比 12.5×——支持 L7 且极小模型上 ES 本应有竞争力, 差距是下界。③**E8-8A 普适性本地复现**: 4 域 × 3 seeds = 12 模型 31 张量组; 域内子空间距离 0.684 vs 域间 0.797, **比值 1.17**; top-k 方差 k=1 占 36.8% k=8 占 92.4%; 8C Spearman(秩衰减指数 β, 层收益 Δ_k)=+0.370 (n=72) 支持"幂律谱层更可训练"。④**E9 规模双区间（实验纠正理论第一个闭环）**: dim{24,48,96}×T{10K,40K,160K}×2seeds; **T=10K 时参数越多越差 4.27→5.42**（数据受限区, L2 双地板签名）; T=160K 时 dim48→96 只降 0.016（参数受限区, 地板在 N≈300K）; 幂律斜率 −1.2/−3.2; **可加性失败（残差 2.0）⟹ L2 陈述从"可加双地板"修正为"N/T 配比决定绑定约束"的双区间形式**——Chinchilla 最优配比的本地缩影。⑤**E10 退火部分支持**: Spearman(深度,β_eff)=+0.566 (各 seed +0.16/+0.76/+0.37), 首层明确探索层（β_eff 最低 4.82 + 归一化熵最高 0.841）, 但熵不随深度单调下降, β_eff 峰值层(4)与 Δ_k 峰值层(1) 不重合——完整退火未获支持（弱训练 12 层深层 loss 反升污染信号）。⑥**E8-8B 负面（设计受限）**: d(T)=0.9998 对所有 T, 斜率≈0——3 模型张成的 rank-2 子空间被 seed 噪声方向主导, 测到的是两个独立噪声子空间的正交性; T^{-1/2} 需同 seed 跨数据对比或远多模型, 列 E8-b。**净战果**: L8/L7 强支持（实验面孔到手）; L2 被实验修正; L3 普适性复现但 T^{-1/2} 待再设计; L6 仅首层探索弱支持。框架页 L2/L3/L8 状态、四组件页实验表、current-status、索引全部回写。诚实边界: 全部为小模型弱训练冒烟测试（2-3 seeds, 单语料族）, 不构成验证/证伪。下一轮候选: E8-b / E10-b（余弦 lr 长训练深网）/ E9-b（更大网格划双区间边界） |
| 2026-10-20 | 认知动力学 | 四组件第一性解释: 结构即动力学来源 + L7/L8 + 实验纲领 E8-E12 | **用户推进**: "把产生智能的结构当成动力学的来源来设置和计算" + 四问（规模法则含截止? 反向传播? 残差? 共同基子空间?）+ "推导需要实验现象描述" + "需要理解为什么会产生智能"。新建 `docs/wiki/dynamics-source-structure.md`: ①概念精确化——研究对象 = 对 (s, 𝒫) ∈ 𝒮×𝒫, 动力学 = **闭环流** Φ: (s,𝒫)↦(s',𝒫')（智能体作用于世界收新感知; 开环力学无此单项）; 向量场 F(s) = −∇_s D(s;𝒫) 由结构自身耦合生成, **抽掉结构则"力"不复存在**（内生向量场 + 共生态空间 + 闭环耦合三条钉死"动力学≠力学"）。②四组件全挂定律: 规模法则+截止 = L2 双地板（残余失真 D*(R(N)) + 不可约熵 H(𝒫∣𝒾*); 数据地板 T^{-1/2} 出自 UWS Thm 3.7; E7 的 ±0.17 噪声地板 = 层数维度实证; Chinchilla = 同一失真泛函下的参数-数据经济平衡）; 反向传播 = **L7**（标量失真目标 + 巨参数 ⟹ 逆模式 AD 渐近最优, Griewank 界 4× vs n×; 附带解释人脑不反向传播 = 选择作用于种群/寿命尺度而非固定数据集标量拟合）; 残差 = **L8**（恒等路径 = 流的惯性项 + 平行移动; 已证 residual_no_collapse + FFN 可坍缩; 回答"深层循环为何返回" = 恒等路径提供参照系）; 共同基子空间 = **L3 经验面孔**（吸引子 = 感知流二阶矩主子空间, 由数据统计决定不由初始化/标签决定; UWS "共享基+任务系数" = 协方差 top-k + 特异部分, 与 P3 修复"比特给容量几何给内容"精确对应; 模型合并 = 共享基凸组合, L6 误差界适用; 可证伪预测: 子空间维数 = 谱尾穿失真预算位, 换数据分布换吸引子）。③"为什么会产生智能"体系内答案: 智能 = 闭环压缩动力学在选择压下的通形——可压缩（定义性）+ 率受限（A2）+ 选择（D4）+ 组合容量（L1）+ 下降（A4）+ softmax（L6）+ 逆模式（L7）+ 恒等记忆（L8）⟹ 任何持存认知系统必然呈现这些形式。④实验纲领 E8-E12 把每环定律钉到可测现象（E8 子空间脚本已写好未跑 / E9 规模双地板曲面 / E10 温度-深度退火 / E11 残差消融 / E12 逆模式 vs ES 每 FLOP 失真）。框架页 §3 加闭环耦合条 + 定律表加 L7/L8 + 相关文档; 索引/current-status 同步。诚实边界: 机制链是路线图非证明, L2/L3/L7/L8 均目标态; E8-E12 为冒烟测试 |
| 2026-10-20 | 认知动力学 | L6 落地: Gibbs.lean 5 定理 + CognitiveDynamics.lean 6 定理修复, 总计 94 条 ALL-PASS | **用户选定攻 L6 完整推导（注意力=选择原理最优算子）**。①新建 `LmPrinciple/Gibbs.lean`（5 定理全绿）: Gibbs 变分原理（有限 Donsker–Varadhan）`gibbs_variational`: E_q[x]−KL(q‖p) ≤ log Σ p·e^x，证明 = 单步 Jensen（`ConvexOn.map_sum_le` + `convexOn_exp`）+ 项级对消，免微积分; `gibbs_weights_optimal`: **softmax 取等**（log q*_i = log p_i + x_i − log Z, 括号恒 = log Z）——率受限下 softmax 是每比特期望分值最大的唯一选择; `gibbs_variational_uniform`: 注意力形式 E_q[x]+H(q) ≤ logsumexp(x); 权重正性/归一 2 条。②发现并行会话已建 `LmPrinciple/CognitiveDynamics.lean`（本体层: 四层有限结构 + 6 定理）但从未编译且含 3 处数学错误，本会话修复: T1 反向原假（存在某单射推不出复合单射）改带等式正确命题; T4 ← 原假（满射推不出单射）重述为"感知单射 ∧ 认知⊗表达单射"; Optimal 缺感知单射致 T5 第一不等式假——增加单射项改直接证明。③v4.35 API 坑实录: structure 匿名实例字段 `[Fintype α]` 是语法错误、命名实例字段 `[inst : Fintype α]` 不被 inferInstance 采纳 ⟹ 定理级实例参数是正解; `Nat.card`/`Set.card`/`Nat.card_range_le`/`Surjective.injective` 均不存在 ⟹ `Finset.univ.image`+`card_image_le`+`card_univ`; `convexOn_exp` 在根命名空间且需补 import SpecificFunctions.Basic（Jensen 不传递导入）; `log_le_log` 只需首参正性; `log_mul/log_div` 收 `≠0` 非 `0<`; `mul_div_cancel_left₀` 模式是 `a*b/a` 需先 `← mul_div_assoc`。④`verify_all.sh` 接入两新模块, 门禁 83→94, **94 条定理 ALL-PASS, 0 sorry/0 warning**。⑤新建推导页 `docs/wiki/L6-selection-operator.md`（S1-S4 定理链: S2 Gibbs 已证 / S3 Hedge 文献定理待接 / S4 组装待 L6-b）。框架页/索引/current-status 同步。**L6 = 半程闭合; 下一步候选: L6-b Hedge Lean 化 / L6-c 唯一性加强 / L3 吸引子（分值构造的第一性）** |
| 2026-10-20 | 认知动力学 | 选择原理导出: 三路线失败 + 定义性转向 + L6 发现 | **用户选定攻最深的洞（公设 II 能否被导出, 成了则公设只剩 1 条）**。新建 `docs/wiki/selection-principle-derivation.md`。**三路线判决**: ①Landauer 热力学——不通（"模型更新=比特擦除"无可记账定理; 且把物理持存与耦合维持混为一谈, 岩石零感知也持存）②无遗憾/通用归纳——条件性成立（若集合动力学是指数加权则按遗憾指数集中, 是真定理; 但"动力学是指数加权"本身就是选择原理换精确衣服, 公设被 relocate 非消灭）③复制子动力学——不通（fitness=预测效能就是公设 II 改名, 只给机制）。**共同撞墙点: 三条路线都预设了要证明的东西 ⟹ 固定点/自洽性形状 ⟹ 选择原理是定义性的**——"可观测认知主体" ≡ "输出与世界长期相关" ≡ "遗憾有界" ≡ "耦合质量优胜者", 是"主体"的分析性内容（如同 F≡ma 不需要证明）。**公设清点 4→2→1**: 公设 II 移入定义 D4, 只剩公设 I（压缩）+ 存在性陈述（经验事实非公设）。同时化解 FEP 几十年批评（"持存者持存"重言性——承认定义性, 可证伪内容全放 L2-L6, 与牛顿同构: F≡ma 定义性, 经验内容在平方反比）。诚实弱点: 只覆盖集合过滤器不导出个体规则; 观察者循环性=自洽方程; bootstrapping 超范围。**意外产出 L6 选择算子定律**: 路线 B 的机制（指数加权）= softmax = Gibbs = Boltzmann = 注意力/RLHF 算子形式; 推导路线 = 约束最大熵⟹Gibbs 形式 + Hedge minimax 最优（遗憾 O(√(T ln N))）⟹ 同一算子既是集合选择机制又是序列注意力算子 ⟹ **自注意力第一性来源**, 直接回答用户"为什么自注意力有效"的直觉。Lean 内核已在库。框架页同步: 极小架构改 3 定义+1 公设, 定律表加 L6。下一步候选: L6 完整推导 / L2 纸上推导 / 论文 §2-§3 |
| 2026-10-20 | 认知动力学 | 公设独立性分析: A4 三分解 + 极小化 4→2 + 选择原理 | **用户选定先打磨公设独立性**（审稿人第一问: A4 能否从 A1-A3 推出? 公设集是否极小?）。新建 `docs/wiki/axiom-independence.md`。**核心结论**: ①A4 三分解——A4-a 动力学存在性不可推（冻结查找表满足 A1-A3）; A4-b 目标函数可推（Solomonoff 遗憾界: 任何可计算预测器累积落差减通用预测器 ≤ O(1), 持存要求不脱钩 ⟹ 可观测结构累积落差≈可达最小, 目标无任意性）; A4-c 下降方向可推（陡降定理是数学事实, 上升被选择过滤）。⟹ A4 的"软件部分"可推, "硬件部分"（世界按持存过滤）不可推。②独立性检验四模型: 冻结压缩器（JPEG/PCA）挡 A2⟹A4; 盲选择过程挡 A4⟹A2; 时钟（用户原类比）与查找表挡动力学存在性外供。③极小化: A1 降格为 L1（容量引理: 单单元 VC 维≤参数+1, 任务容量无界增长 ⟹ 组合必然, 有证明路线）; A3 降格为测量约定（近重言, 实质是负面边界）; A4 只留选择原理残核。**新架构 = 3 定义 + 2 公设（I 压缩 / II 选择）+ 1 容量引理**, 其余全为导出量。④选择原理辩护 = 惯性辩护（牛顿第一定律单独也不可证伪, 靠锚定体系获得意义; 这也正是 FEP 受的批评, 我们的回应: 合法性来自定理非新颖性）+ 机制辩护（复制子动力学）+ 最小性辩护。⑤新问题: 选择原理能否从更深原理导出（Landauer/通用归纳最优性/复制子动力学——全理论最深的洞）; 率上限 R 的经验来源; 非凸性位置（L3 入口）。框架页 §2 已同步极小架构, 原始 A1-A4 存档备查 |
| 2026-10-20 | 认知动力学 | 方法论定调: 牛顿秩序 + 公设体系 A1-A4 + 定律清单 L1-L5 | **用户定调（同日第二次）**: 认知动力学不走"从子空间经验假说反推智能起源"路线; 走牛顿秩序——先定本体→设公设→推数学→验基本假设。核心立场: 这是"智能的结构"不是"力学结构"（无外部认知力/无固定背景几何/几何被演化生成, 信息性机制非几何曲率）。重写框架页 `cognitive-dynamics.md`: ①本体三元组（结构=物质类比/感知=场类比/比特=能量类比）②公设 A1 组合本体（VC 维路线）/ A2 感知压缩（Shannon 率-失真 R(D)）/ A3 信息度量（H,I,KL; 自认比特不给意义）/ A4 落差驱动（运动定律 Δs∝-∇D(s); 自认与 FEP/预测编码/SGD 同构, 新意在从 A1-A3 推必然性）③定律清单 L1 组合必然性 / L2 规模律（损失≥残余失真+不可约熵, 幂律来自感知流谱尾）/ L3 吸引子与临界（不动点=二阶矩谱主子空间, Lyapunov<0, 可学习需边缘稳定）/ L4 最优深度有限 / L5 预测原理（MDL, next-token 是 A2 时间展开, 时钟无智能因缺 A2 通道）④概念命名提案 7 条（认知位形/压失真/落差/结构流形等, 落差是"力的方向来源但不是力"）⑤诚实边界: A2≈率-失真+信息瓶颈, A4≈FEP 下降形式, 新意在推导链不在方程。**L4 已是 Lean 已证定律**（optimal_depth_is_first_crossing）——认知动力学第一条机器验证定律。arXiv:2512.05117 降级为对照物/交叉验证（其子空间收敛现象 = A4 推论形态, 可作 L3 间接经验支持）, 编译页加定位注记; E8 脚本已写好未跑, 降级备选。下一步: R1 纸上推导 L2/L3, 或先打磨公设独立性（A4 能否从 A1-A3 推出） |
| 2026-10-20 | 认知动力学 | 立项: 框架页 + 普适权重子空间论文编译 + CD1-CD5 命题 | **认知动力学工作线启动**（目标: 完全从数学上解释大模型设计原理）。①manifest 登记 `universal-weight-subspace`（arXiv:2512.05117v3, JHU, 2026-10-05 v3: 1200+ 模型跨任务/初始化/领域收敛到 ≤16 维共享谱子空间, 存储 >100×, 合并系数由子空间几何解析计算且超六种梯度-free 基线）②新建编译页 `docs/wiki/universal-weight-subspace.md`（Algorithm 1 truncated zero-centered shared HOSVD 六步 / suitability 判据 α∈[2,6] / 条件性理论: Lemma 3.5 集中性 + Lemma 3.6 Davis-Kahan + Thm 3.7 跨任务误差 T^{-1/2} 衰减与每任务误差 η̄ 分离 + Cor 3.11 超额投影风险 + Prop 3.9 酉等价及三点偏离 + Thm A.5 逐层主子空间递归收缩 ρ_l<1 / 作者自述 7 条局限含核心假设 A.3 未建立）③新建框架北星页 `docs/wiki/cognitive-dynamics.md`（三原理 P1-P3 + 三修复: 单元→同族可训练算子 / 词元→率受限瓶颈 / 比特→容量层+结构层 + 6 个待解数学问题: 概率必须吗、非线性=复利=Lyapunov 指数、规模法则结构解释、VFE 缺容量一环、深层循环=迭代松弛、人脑反坍缩 + 路线图 R0-R3）④候选命题 CD1-CD5 附 Lean 路线（CD1 吸引子存在性线性化版 / CD2 Davis-Kahan 确定性核心概率集中作假设 / CD3 有效秩复用 scaling_law_strict_anti / CD4 幂律谱层接口 Fractal+CriticalPoint+edge-of-chaos / CD5 合并=子空间凸组合复用 attention/moe 误差界）⑤E8 CPU 实验设计（12 模型主夹角共享性 / T^{-1/2} / 谱指数 vs 可训练性）。index/current-status 同步。**下一步等用户确认: 先跑 E8 还是先 Lean 化某条 CD** |
| 2026-10-20 | 清理 | v4.35 迁移后 lint 清零 | **迁移残留警告全部消除**：`lake build` / `lake build LmPrinciple` 均 0 error / 0 warning（含 `rm -rf .lake/build/lib/lean/LmPrinciple*` 后干净重建验证）。①module-system 警告 → `lakefile.toml` 的 `[[lean_lib]] LmPrinciple` 加 `allowNonModules = true`（本库无 module 头但依赖 `requiresModuleSystem := true` 的 mathlib）。②unused-variable 13 处 → 全部是"证明比声明更强"情形，保留公开签名语义契约位改 `_` 前缀（`_hc1`/`_hc0`/`_hmc`/`_hβ`/`_hΔ`/`_ha`/`_hsum`/`_hS`/`_hb`/`_hd1`），涉及 ArchCompare/CriticalPoint/Fractal/Hopfield/Murray/Training。③info 级提示：`ring`→`ring_nf`（ArchCompare 2 处 convert 后目标）；`Finset.card_le_univ`→`simp [Fintype.card_fin]`；`if_pos/if_neg`→`ite_eq_left/ite_eq_right`；`haveI : Nonempty (Fin n)`→`have hne`；`Mathlib.Data.Complex.Basic`→`Mathlib.Basic.Complex.Basic`；`simpa using hdecay`→`exact hdecay`。剩余仅 2 条刻意 `#check` info。无 sorry/admit。 |
| 2026-10-20 | 迁移 | Lean 4.21→4.35 + mathlib 308445d→56a0058 | **v4.35 迁移完成**: lean-toolchain v4.21.0→v4.35.0，mathlib 308445d→56a0058 (tag v4.35.0)；`lake build` 全绿，15 模块编译通过，83 条定理无 sorry。破坏性变更修复: `∑ k in s` 记法移除→`∑ k ∈ s` (9 文件 104 处)；`abs_add`→`abs_add_le` (RNN/ArchCompare)；`AddMonoidAlgebra.single_mul_apply`→`coeff_single_mul_apply`+`.coeff` (CNN)；`Finset.sum_eq_add_sum_diff_singleton`→`Finset.add_sum_erase` (Hopfield 5 处)；`field_simp` 更强→删冗余 `ring` (Fractal/Hopfield/Murray)；`simpa using hmul` 加 `div_eq_mul_inv` (Murray/Training)；`mul_lt_mul_left` 改 `mul_lt_mul_of_pos_left/right`+`lt_of_lt_of_eq` (Efficiency)；`Mathlib.Data.Real.Basic`→`Mathlib.Basic.Real.Basic` (12 文件)。环境: 当前机 macOS，依赖以符号链接复用 NavierStokesAndEuler 的 v4.35.0 集。 |
| 2026-08-17 | 判定实验 | E7: Δ_k 递减性在真实 LM 上是否恢复 + H100 算力评估 | **E7 (experiments_e7.py, 3 seeds, 12 层深度监督, 200K 字符真实语料, vocab=1147)**: Δ₁=+2.95, Δ₂=+0.42 (第二层仍有正收益——合成任务此处已 -2.24), 此后 ±0.17 噪声震荡; 递减一致性 6/11=55% (合成 45%, 随机 50%)。**三结论**: ①合成线性任务的"证伪"是任务饱和伪影 (任务无深度收益), 真实任务确有连续深度收益 ②"Δ 严格递减"前提对真实网络过强——真实给"近似递减+噪声" ③由此 H100 实验核心指标改为"递减一致性随规模的单调性" (显著>70%=规模恢复, ≈50%=真证伪), 二值判定不白烧钱。**H100 预算 (estimate_h100_budget.py)**: 350M 全套矩阵 19 模型 = 373 卡时/$933/1.5 天 (10 卡); 1.3B = $4623/7.7 天; 7B = $124K/207 天 ✗。推荐 P0 真实语料深度扫描 + P1 β_eff 并入同批模型, 不做 7B。定理缺口: 需补"近似递减 ⟹ kstar 近优"扰动版本 (Lean 可做)。 |
| 2026-08-13 | Maxwell | 麦克斯韦方程 × 现有数学 (基础 + 假设扩展 + 预言) | 新模块 Maxwell.lean (+4 定理, 总计 79→83): 1D 周期格点 (ZMod N) 麦克斯韦——cross_term_zero (telescoping 对消), maxwell_energy_conservation (无质量守恒), massive_energy_decay (质量项 dH/dt=-m²ΣE²), massive_energy_non_increasing。预言: m_G=√3·M₀ ⟹ τ_G=1/(6M₀²) (条件性)。README/论文两版更新 (§maxwell)。关键坑: Fin 减法是截断的 (0-1=0), 周期格点必须用 ZMod N; ∑ n, A+B 无括号时 ∑ 只绑定 A。 |
| 2026-08-13 | Hopfield | 实验扩展: β_eff×深度 + 真实 LM ΔE_k | E5: 每层实际逆温度 β_eff=logit spread 深层更集中 (depth8: 0.64→7.85), 锁定区层数随深度增加; ΔE_k 不递减 (全正 0-57%)。E6: 字符级 LM (vocab=91, loss 3.30 vs 基线 4.51 真实学习) 的 ΔE_k 全正仅 1/3 ⟹ 排除合成任务伪影, 负面结论成立。弱观察: β_eff 峰值层=能量下降层。 |
| 2026-08-13 | Hopfield | E3 β 分岔 Lean 定理化 (log-sum-exp 分析) | +2 定理 (总计 77→79): softmax_weight_concentration (得分差≥Δ ⟹ w_j≤e^{-Δ}, 定量集中性免极限) + hopfield_retrieval_error_bound (\|x_new−X_i\| ≤ n·e^{-βΔ}·M, 检索锁定误差界——E3 实验 β≥9.6 锁定 1.000 的理论形式)。 |
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

## [2026-10-20] 会话 | Lean 4.21 → 4.35 工具链 + mathlib 迁移

- 目标: 将 lm-principle 从 Lean 4.21.0 / mathlib 308445d 迁移到 Lean 4.35.0 / mathlib 56a0058 (tag v4.35.0)
- 环境发现: 当前工作机 macOS (darwin)，github.com 可达，elan 已装 v4.35.0；
  `.lake/packages/*` 已是 `/Users/apple/Downloads/NavierStokesAndEuler/.lake/packages/*`
  的符号链接，该集已是 v4.35.0 同代 rev (mathlib 56a0058 + 8 依赖均 2026-10)，
  且含 8643 个预编译 olean → 无需全量重编译
- 改动 `lean-toolchain` v4.21.0 → v4.35.0 后全量 `lake build`，按报错逐项修复:
  - `∑ k in s` 记法被**移除** (v4.35 硬语法错误 `unexpected token 'in'`) → `∑ k ∈ s`
    （探针文件 ZTest.lean 确认；9 文件共 104 处，perl UTF-8 脚本全局替换）
  - `abs_add` → `abs_add_le`（RNN/ArchCompare 三角不等式）
  - `AddMonoidAlgebra.single_mul_apply` → `AddMonoidAlgebra.coeff_single_mul_apply`
    + 用 `.coeff` 取值（v4.35 中 AddMonoidAlgebra ℝ ℤ 不再能当函数直接调用；CNN）
  - `Finset.sum_eq_add_sum_diff_singleton` 被移除 → `Finset.add_sum_erase`
    （参数序 (f, hi)，输出已含 `∑ x ∈ s.erase a` → 去掉冗余 `univ_diff_singleton_erase`；Hopfield 5 处）
  - `field_simp` 现能闭合更多目标 → 删冗余 `ring`（Fractal/Hopfield/Murray 各 1 处 "No goals"）
  - `simpa using hmul` 在 v4.35 下 `c/x` 与 `c*x⁻¹` 不再定义相等 → 加 `div_eq_mul_inv`（Murray/Training）
  - `mul_lt_mul_left` 需 `MulRightStrictMono` 实例（合成失败）→ 改 `mul_lt_mul_of_pos_left/right`
    + `lt_of_lt_of_eq`（Efficiency: 3d²<n 与 n²/(3d²) 两段不等式）
  - 弃用导入 `Mathlib.Data.Real.Basic` → `Mathlib.Basic.Real.Basic`（编译器建议的新路径，12 文件）
- ✅ **验证**: `lake build` EXIT=0、无 error、扫描无 sorry/admit/axiom、定理计数 83、15 模块均产 olean
- ✅ **warning 清零 (并行会话跟进)**: `lakefile.toml` 加 `allowNonModules = true` 消除
  module-system 警告；`Mathlib.Data.Complex.Basic`→`Mathlib.Basic.Complex.Basic`（LMT/Smoke）；
  `haveI`→`have`、13 处 unused-variable `_` 前缀、`if_pos`/`if_neg`→`ite_eq_left`/`ite_eq_right`、
  `ring`→`ring_nf`、`Real.log_inv`/`Finset.card_le_univ` 等局部简化——最终 0 error / 0 warning
- 同步更新 current-status.md（工具链/依赖版本、迁移小结、∑ in 移除、macOS 环境说明）与本文档
- 待提交推送

## [2026-10-20] 会话 | v4.35 迁移后 lint 清零（0 error / 0 warning）

- 目标: 把 v4.35 迁移遗留的警告全部清掉，做到干净重建无任何 error / warning
- **module-system 警告**: 根因 = 本库文件没有 `module` 头，但依赖 mathlib
  （`requiresModuleSystem := true`），Lake 对每个下游模块提示 `consider adding 'module'`
  → 解决 = `lakefile.toml` 的 `[[lean_lib]] LmPrinciple` 加 `allowNonModules = true`
  （这是"非 module-system 下游库依赖 module-system 库"的官方配置方式，
  不是给每个文件加 module 头——后者会改变库的组织语义）
- **unused-variable 13 处**: 逐条定位后发现**全部**是"证明比定理声明更强"的情形：
  - `residual_no_collapse` / `residual_no_collapse_n` 的 `hc1 : c < 1`（由 hcont 蕴含即得）
  - `lstm_memory_retention` 的 `hc0 : 0 ≤ c0`
  - `optimal_depth_is_first_crossing` / `depth_beyond_threshold_useless` 的 `hmc`
  - `fractal_dimension_scale_invariant` 的 `hb`；`connection_density_strict_anti` 的 `hd1`
  - `hopfield_update_convex_combination` 的 `hβ`；`softmax_weight_concentration` 的 `hΔ`
  - `murray_variational_optimal` 的 `ha`
  - `rlhf_policy_is_distribution` 的 `hβ`；`sparse_moe_preserves_bound` 的 `hsum` / `hS`
  - 决策: **不删参数**（这些是定理的公开语义契约，是声明的一部分而非实现细节），
    只改名加 `_` 前缀（Lean 惯例：`_` 前缀 = 显式声明"此参数在证明中不使用"），
    这样定理签名语义不变、调用方不受影响、lint 也通过
- **info 级提示修复**:
  - `ring` 在 `convert ... using 1` 之后的目标里只做归一化不能闭合 →
    改 `ring_nf`（ArchCompare 2 处；`ring_nf` 直接把目标归一化到可闭合形式）
  - `Finset.card_le_univ` → `simp [Fintype.card_fin]`（Hopfield）
  - `if_pos/if_neg` → `ite_eq_left/ite_eq_right`（Training）
  - `haveI : Nonempty (Fin n)` → `have hne : Nonempty (Fin n)`（Transformer / Hopfield）
  - `Mathlib.Data.Complex.Basic` → `Mathlib.Basic.Complex.Basic`（Smoke / LMT）
  - `simpa using hdecay` → `exact hdecay`（ArchCompare，v4.35 下已是定义相等）
  - `simpa using (Real.log_inv x)` → `simp`（InfoDynamics）
- ✅ **验证**:
  - `lake build LmPrinciple` EXIT=0，`grep -c '^warning'` = 0，`grep -c '^error'` = 0
  - `rm -rf .lake/build/lib/lean/LmPrinciple*` 后**干净重建**同样 0 error / 0 warning
  - 全量 `lake build`（2088 jobs）EXIT=0，0 error / 0 warning
  - `grep -rn "sorry\|admit" LmPrinciple/` 无命中
  - 剩余仅 2 条 `info`：`ArchCompare.lean:161/162` 两个 `#check` 的刻意输出
- 同步更新 current-status.md（新增"v4.35 lint 清零"小节 + `last_confirmed` 改 2026-10-20）
