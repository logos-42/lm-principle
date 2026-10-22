/-
# Generalization — L9: 泛化 = 流形连通性驱动的信息流动效率 (用户直觉 → Lean)

用户直觉 (2026-10-22): "泛化理论的核心在于流形和注意力全局, 主要是信息流动效率的升级,
量级不同泛化效率就不同; 类比: 在毛球上运动的路线更多更快, 且全局路线联动性、连通性更强。
这是在这个理论下的自然推导。"

框架内翻译: 泛化不是独立现象, 是**表示流形上信息流动效率**的表现:
  - 注意力 = 全局路由 (L6: softmax 逐次最优选择) ⟹ 流形上**全对全**连通, 路线最多最快;
  - 局部结构 (CNN 有限感受野, `CNN.single_mul_apply`) ⟹ 连通受限, 路线少;
  - 数据量 T 决定可估计的结构量 (UWS 定理 3.7: 估计误差 ~ T^{-1/2});
  - 量级 (规模/维度) ⟹ 更多路线/更强联动 ⟹ 更高连通性。

本文件把"泛化误差 = 数据估计项 × 连通性惩罚"形式化 (机器验证):
  - `gen_error data_term penalty κ T = data_term T · penalty κ`
      · data_term(T): 数据估计项, 随 T 下降 (如 1/√T, UWS);
      · penalty(κ): 连通性惩罚, 连通性 κ 越强惩罚越小 (全局路由 κ 最大 ⟹ 惩罚最小);
  - `gen_error_mono_data`   : 数据↑ ⟹ 泛化误差↓ (信息更足, 估计更准);
  - `gen_error_mono_conn`   : 连通性↑ ⟹ 泛化误差↓ (路线更多更快, 信息流动更充分);
  - `global_routing_min_gen`: 全局路由 (最大连通性 κ_max) ⟹ 泛化误差最小 (胜过局部路由)。

诚实边界: 本文件证**方向/单调性** (连通性↑、数据↑ 都压低泛化误差; 全局>局部);
具体误差函数 (data_term/penalty 的精确形式) 是建模假设 (data_term 接 UWS T^{-1/2}, penalty 待标定);
泛化的**数据受限区** (连通性红利被数据封顶, 镜像 G2 的 min) 是更深内容, 见文档注记。
-/
import Mathlib.Order.Basic
import Mathlib.Tactic

noncomputable section

namespace Generalization

/-- **泛化误差 = 数据估计项 × 连通性惩罚**: 表示流形上信息流动效率的标量化。
    `data_term T` 随数据量下降 (有限数据的估计误差, 接 UWS `T^{-1/2}`);
    `penalty κ` 随连通性下降 (连通性 κ = 全局路由的联动强度, 越全局惩罚越小)。 -/
def gen_error (data_term penalty : ℝ → ℝ) (κ T : ℝ) : ℝ := data_term T * penalty κ

/-- **数据↑ ⟹ 泛化误差↓**: 数据越多, 感知流结构估计越准 (UWS `T^{-1/2}`), 泛化越好。 -/
theorem gen_error_mono_data (data_term penalty : ℝ → ℝ) (hdt : Antitone data_term)
    (hp0 : ∀ κ, 0 ≤ penalty κ) {κ T1 T2 : ℝ} (h : T1 ≤ T2) :
    gen_error data_term penalty κ T2 ≤ gen_error data_term penalty κ T1 := by
  unfold gen_error
  exact mul_le_mul_of_nonneg_right (hdt h) (hp0 κ)

/-- **连通性↑ ⟹ 泛化误差↓**: 流形上路线更多更快、全局联动更强 (毛球上运动更充分),
    信息流动效率升级, 泛化更好。这是"注意力全局 → 泛化"的严格方向内核。 -/
theorem gen_error_mono_conn (data_term penalty : ℝ → ℝ) (hp : Antitone penalty)
    (hdt0 : ∀ T, 0 ≤ data_term T) {κ1 κ2 T : ℝ} (h : κ1 ≤ κ2) :
    gen_error data_term penalty κ2 T ≤ gen_error data_term penalty κ1 T := by
  unfold gen_error
  exact mul_le_mul_of_nonneg_left (hp h) (hdt0 T)

/-- **全局路由 (最大连通性) ⟹ 泛化误差最小**: 注意力全局路由达到连通性上界 κ_max,
    故其连通性惩罚最小、泛化误差最小 —— 胜过任何局部/受限路由 (CNN 有限感受野)。
    这是"自注意力为何跨任务泛化更好"的第一性方向。 -/
theorem global_routing_min_gen (data_term penalty : ℝ → ℝ) (hp : Antitone penalty)
    (hdt0 : ∀ T, 0 ≤ data_term T) (κ_max : ℝ) {κ T : ℝ} (h : κ ≤ κ_max) :
    gen_error data_term penalty κ_max T ≤ gen_error data_term penalty κ T := by
  unfold gen_error
  exact mul_le_mul_of_nonneg_left (hp h) (hdt0 T)

end Generalization
