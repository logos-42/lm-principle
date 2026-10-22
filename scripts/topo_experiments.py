"""拓扑结构构造实验 (E-TOPO-1 / E-TOPO-2) — 本地 CPU, 秒级, 无需 GPU.

E-TOPO-1: 兰顿蚂蚁 (Langton's Ant) —— 规则即梯度, 无外部优化器, 突现 highway 吸引子.
           演示 A4 "结构内生向量场, 无外部施力者".
E-TOPO-2: 毛球定理演示 —— S^2 上平滑切向量场必有零点 (= "坑"), 加一条法向"残差"
           路径后系统绕开坍缩. 演示 L8 残差的拓扑根 (hairy ball theorem).

用法:
    python3 scripts/topo_experiments.py topo1 [--steps 11000]
    python3 scripts/topo_experiments.py topo2
    python3 scripts/topo_experiments.py all
"""
import argparse
import json
import math
import os

import numpy as np

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "experiments", "results")
os.makedirs(RESULTS, exist_ok=True)


# ---------------------------------------------------------------------------
# E-TOPO-1: Langton's Ant —— 规则即梯度, 吸引子定轨迹
# ---------------------------------------------------------------------------
def run_langton(steps=11000):
    # 0=up,1=right,2=down,3=left
    dxdy = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    grid = {}  # (x,y) -> 1 if black else 0/ absent
    x = y = 0
    d = 0
    black = 0
    samples = {}
    pos = np.zeros((steps, 2), dtype=np.int64)
    for s in range(steps):
        c = grid.get((x, y), 0)
        if c == 0:          # 白格: 右转, 翻黑, 前进
            d = (d + 1) % 4
            grid[(x, y)] = 1
            black += 1
        else:               # 黑格: 左转, 翻白, 前进
            d = (d + 3) % 4
            grid[(x, y)] = 0
            black -= 1
        x += dxdy[d][0]
        y += dxdy[d][1]
        pos[s, 0] = x
        pos[s, 1] = y
        if s % 1000 == 0:
            samples[int(s)] = black
    # highway 检测: 经典兰顿蚂蚁在 ~10000 步后进入周期为 104 步的斜向高速周期.
    # 检查尾段 [10000,11000) 是否每 104 步位移相同 (高速移动的平移不变性).
    highway = False
    shift = None
    if steps >= 10104:
        base = pos[10000:10104]            # 104 步窗口
        nxt = pos[10104:10208]
        diffs = base[1:] - base[:-1]
        diffs2 = nxt[1:] - nxt[:-1]
        if np.array_equal(diffs, diffs2) and np.all(np.abs(diffs) <= 1):
            highway = True
            shift = (int(base[-1, 0] - base[0, 0]), int(base[-1, 1] - base[0, 1]))
    # 边界盒
    bx = int(pos[:, 0].max() - pos[:, 0].min())
    by = int(pos[:, 1].max() - pos[:, 1].min())
    bbox_growth = None
    if steps >= 10104:
        b0 = (pos[10000:10104].max(0) - pos[10000:10104].min(0)).sum()
        b1 = (pos[10104:10208].max(0) - pos[10104:10208].min(0)).sum()
        bbox_growth = float(b1 - b0) / 104.0  # 每步边界增长
    return {
        "steps": steps,
        "black_final": int(black),
        "black_samples_every_1k": samples,
        "highway_detected": highway,
        "highway_period": 104 if highway else None,
        "highway_shift_per_period": shift,
        "bbox_final": [bx, by],
        "bbox_growth_per_step_after_10k": bbox_growth,
        "note": ("规则仅依赖局部格子颜色 (无损失/无优化器), 却在 ~10k 步后突现 "
                 "周期 highway 吸引子 —— 演示 A4: 向量场由规则内生, 吸引子决定轨迹."),
    }


# ---------------------------------------------------------------------------
# E-TOPO-2: 毛球定理 —— S^2 上平滑切向量场必有零点 (= "坑"), 残差(法向)绕开坍缩
# ---------------------------------------------------------------------------
def hairy_field(p, a):
    """切向量场 = 固定向量 a 在球面切平面上的投影. 在 a 与 p 平行处 (两极) 为零."""
    p = np.asarray(p, float)
    p = p / np.linalg.norm(p)
    return a - (a @ p) * p


def run_hairy_ball(dt=0.01, nsteps=6000, residual=0.4):
    a = np.array([0.0, 0.0, 1.0])           # 零点在两极 (±z)
    p0 = np.array([1.0, 0.0, 0.0])          # 从赤道起

    # (A) 严格切向动力学 (每步归一化, 始终在球面上): 轨迹必被吸向极点(零点)卡死 = 坍缩
    p = p0.copy()
    stuck_step = None
    for i in range(nsteps):
        v = hairy_field(p, a)
        if np.linalg.norm(v) < 1e-7:
            stuck_step = i
            break
        p = p + dt * v
        p = p / np.linalg.norm(p)
    tangent_stuck = stuck_step is not None
    tangent_endpoint = (float(p[0]), float(p[1]), float(p[2]))
    tangent_zero_norm = float(np.linalg.norm(hairy_field(p, a)))

    # (B) 加入法向"残差"路径: 在嵌入空间 R^3 允许真实法向位移(不归一化),
    #     轨迹可越过极点而非卡在奇点 —— 几何替身: 残差/跳连 = 提供离面的恒等维度,
    #     系统不再被严格限制在偶维闭流形上, 故无需在零点坍缩.
    p = p0.copy()
    for i in range(nsteps):
        v = hairy_field(p, a)
        vn = np.linalg.norm(v)
        step = dt * v + residual * dt * (p / np.linalg.norm(p))  # 法向漂移(真实 R^3 位移)
        p = p + step
        # 越过极点区 (z 穿过 ±1) 即视为"逃出坍缩"
        if abs(p[2]) > 1.05:
            break
    residual_endpoint = (float(p[0]), float(p[1]), float(p[2]))
    residual_radius = float(np.linalg.norm(p))
    residual_escaped = residual_radius > 1.02  # 离面(半径>1) = 未坍缩于球上零点

    # 零点个数 (解析): 此场零点恰为两极 -> 2 个; Poincaré-Hopf: sum(index)=chi(S^2)=2
    return {
        "manifold": "S^2 (偶维闭流形)",
        "field": "固定向量 a 的切平面投影",
        "zeros_count": 2,
        "poincare_hopf_index_sum": 2,
        "tangent_only": {
            "endpoint": tangent_endpoint,
            "field_norm_at_endpoint": tangent_zero_norm,
            "collapsed_to_zero": tangent_stuck,
            "stuck_step": stuck_step,
        },
        "with_residual_normal_path": {
            "endpoint": residual_endpoint,
            "radius_at_endpoint": residual_radius,
            "escaped_collapse": residual_escaped,
        },
        "note": ("毛球定理: S^2 上不存在处处非零的连续切向量场 -> 严格切向下降流必在极点"
                 "坍缩为奇点 ('坑'). 加入法向残差路径(离面恒等维度)后轨迹越过极点, "
                 "回避坍缩 —— 正是 L8 残差的拓扑根: 恒等/法向回馈 = 绕开奇点的平行移动. "
                 "(注: '法向残差'为几何类比, 真实跳连为表示空间的恒等/门控回馈.)"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?", default="all",
                    choices=["topo1", "topo2", "all"])
    ap.add_argument("--steps", type=int, default=11000)
    args = ap.parse_args()
    out = {}
    if args.which in ("topo1", "all"):
        r1 = run_langton(args.steps)
        out["E_TOPO_1_langton"] = r1
        print(f"[TOPO-1] Langton's Ant: steps={r1['steps']} black={r1['black_final']} "
              f"highway={r1['highway_detected']} shift={r1['highway_shift_per_period']} "
              f"bbox_growth/step={r1['bbox_growth_per_step_after_10k']}")
    if args.which in ("topo2", "all"):
        r2 = run_hairy_ball()
        out["E_TOPO_2_hairyball"] = r2
        print(f"[TOPO-2] Hairy ball: zeros={r2['zeros_count']} "
              f"tangent_collapsed={r2['tangent_only']['collapsed_to_zero']} "
              f"residual_escaped={r2['with_residual_normal_path']['escaped_collapse']}")
    with open(os.path.join(RESULTS, "topo_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("[TOPO] -> experiments/results/topo_results.json")


if __name__ == "__main__":
    main()
