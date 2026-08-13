# -*- coding: utf-8 -*-
"""
本地真实实验: 分形 vs 均匀 Transformer + 最优深度扫描
(基于 shape.md 第三季第3期配套代码, 本地 torch CPU 真实运行)

输出: experiments/results/fractal_experiments.json (真实本地数据)
"""
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

torch.manual_seed(42)
np.random.seed(42)


class FractalTransformerLayer(nn.Module):
    """分形Transformer层: 不同层有不同的计算特性 (与文章代码一致)"""

    def __init__(self, dim=64, heads=4, is_deep=False, connection_density=1.0):
        super().__init__()
        self.dim = dim
        self.is_deep = is_deep
        actual_heads = max(2, heads if not is_deep else heads // 2)
        self.attn = nn.MultiheadAttention(dim, actual_heads, batch_first=True)
        ff_ratio = 4 if not is_deep else max(1, int(4 * connection_density))
        self.ff = nn.Sequential(
            nn.Linear(dim, dim * ff_ratio),
            nn.ReLU(),
            nn.Linear(dim * ff_ratio, dim)
        )
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)

    def forward(self, x):
        attn_out, _ = self.attn(x, x, x)
        x = self.norm1(x + attn_out)
        ff_out = self.ff(x)
        x = self.norm2(x + ff_out)
        return x


class UniformTransformer(nn.Module):
    """均匀Transformer: 所有层结构完全一致 (与文章代码一致)"""

    def __init__(self, dim=64, heads=4, n_layers=8):
        super().__init__()
        self.layers = nn.ModuleList([
            FractalTransformerLayer(dim, heads, is_deep=False, connection_density=1.0)
            for _ in range(n_layers)
        ])
        self.embed = nn.Linear(10, dim)
        self.output = nn.Linear(dim, 1)

    def forward(self, x):
        x = self.embed(x)
        for layer in self.layers:
            x = layer(x)
        x = x.mean(dim=1)
        return self.output(x).squeeze(-1)


class FractalTransformer(nn.Module):
    """分形Transformer: 层特性按分形缩放 (与文章代码一致)"""

    def __init__(self, dim=64, heads=4, n_layers=8, fractal_dim=2.5):
        super().__init__()
        self.layers = nn.ModuleList()
        for i in range(n_layers):
            depth_ratio = i / max(1, n_layers - 1)
            connection_density = (1 - depth_ratio) ** (fractal_dim - 1)
            is_deep = depth_ratio > 0.5
            self.layers.append(
                FractalTransformerLayer(dim, heads, is_deep=is_deep,
                                       connection_density=connection_density)
            )
        self.embed = nn.Linear(10, dim)
        self.output = nn.Linear(dim, 1)

    def forward(self, x):
        x = self.embed(x)
        for layer in self.layers:
            x = layer(x)
        x = x.mean(dim=1)
        return self.output(x).squeeze(-1)


def make_data():
    X_train = torch.randn(800, 20, 10)
    y_train = (X_train[:, :, 0].sum(dim=1) * 2 + X_train[:, :, 1].sum(dim=1) * 1.5
               + torch.randn(800) * 0.3)
    X_test = torch.randn(200, 20, 10)
    y_test = (X_test[:, :, 0].sum(dim=1) * 2 + X_test[:, :, 1].sum(dim=1) * 1.5
              + torch.randn(200) * 0.3)
    return X_train, y_train, X_test, y_test


def train_and_evaluate(model, X_train, y_train, X_test, y_test, n_epochs, seed=42):
    # 与文章一致: 全局 seed 流连续推进 (不在此重置, 保持可复现性)
    opt = optim.Adam(model.parameters(), lr=0.005)
    crit = nn.MSELoss()
    history = []
    t0 = time.time()
    for ep in range(n_epochs):
        opt.zero_grad()
        loss = crit(model(X_train), y_train)
        loss.backward()
        opt.step()
        with torch.no_grad():
            test_loss = crit(model(X_test), y_test).item()
            history.append(test_loss)
        if (ep + 1) % 20 == 0 or ep == n_epochs - 1:
            print(f"      epoch {ep+1}/{n_epochs}: test_loss={test_loss:.4f}")
    dt = time.time() - t0
    return history, dt


def run_experiment2(X_train, y_train, X_test, y_test, n_epochs=100):
    """实验二: 分形 vs 均匀 Transformer (dim=64, heads=4, 8层)"""
    print("\n[实验二] 分形 vs 均匀 Transformer (dim=64, heads=4, n_layers=8)")
    torch.manual_seed(42)
    uniform_model = UniformTransformer(dim=64, heads=4, n_layers=8)
    fractal_model = FractalTransformer(dim=64, heads=4, n_layers=8, fractal_dim=2.5)
    p_u = sum(p.numel() for p in uniform_model.parameters())
    p_f = sum(p.numel() for p in fractal_model.parameters())
    print(f"  均匀参数量: {p_u}")
    print(f"  分形参数量: {p_f}")
    print(f"  训练均匀 (100 epochs)...")
    h_u, t_u = train_and_evaluate(uniform_model, X_train, y_train, X_test, y_test, n_epochs)
    print(f"  训练分形 (100 epochs)...")
    h_f, t_f = train_and_evaluate(fractal_model, X_train, y_train, X_test, y_test, n_epochs)
    result = {
        "experiment": 2,
        "uniform_params": p_u,
        "fractal_params": p_f,
        "uniform_final_loss": h_u[-1],
        "fractal_final_loss": h_f[-1],
        "uniform_train_seconds": round(t_u, 1),
        "fractal_train_seconds": round(t_f, 1),
        "uniform_history_sampled": [round(x, 4) for x in h_u[::10]],
        "fractal_history_sampled": [round(x, 4) for x in h_f[::10]],
    }
    print(f"  均匀最终损失: {h_u[-1]:.4f} | 分形最终损失: {h_f[-1]:.4f}")
    print(f"  均匀训练耗时: {t_u:.1f}s | 分形训练耗时: {t_f:.1f}s")
    return result


def run_experiment3(X_train, y_train, X_test, y_test, n_epochs=80):
    """实验三: 最优深度搜索 (dim=32, heads=2)"""
    print("\n[实验三] 最优深度搜索 (dim=32, heads=2)")
    depths = [2, 4, 6, 8, 10, 14, 18]
    uniform_results, fractal_results = [], []
    for n_layers in depths:
        print(f"  {n_layers}层...")
        u_model = UniformTransformer(dim=32, heads=2, n_layers=n_layers)
        h_u, _ = train_and_evaluate(u_model, X_train, y_train, X_test, y_test, n_epochs)
        uniform_results.append(h_u[-1])
        f_model = FractalTransformer(dim=32, heads=2, n_layers=n_layers, fractal_dim=2.5)
        h_f, _ = train_and_evaluate(f_model, X_train, y_train, X_test, y_test, n_epochs)
        fractal_results.append(h_f[-1])
        print(f"    {n_layers:2d}层: 均匀={h_u[-1]:.4f}, 分形={h_f[-1]:.4f}")
    result = {
        "experiment": 3,
        "depths": depths,
        "uniform_losses": [round(x, 4) for x in uniform_results],
        "fractal_losses": [round(x, 4) for x in fractal_results],
        "uniform_optimal_depth": depths[int(np.argmin(uniform_results))],
        "fractal_optimal_depth": depths[int(np.argmin(fractal_results))],
    }
    return result


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    X_train, y_train, X_test, y_test = make_data()
    results = {}
    results["exp2"] = run_experiment2(X_train, y_train, X_test, y_test, n_epochs=100)
    results["exp3"] = run_experiment3(X_train, y_train, X_test, y_test, n_epochs=80)
    results["meta"] = {
        "torch": torch.__version__,
        "device": "cpu",
        "seed": 42,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    out_path = os.path.join(out_dir, "fractal_experiments.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {out_path}")
    print("=" * 60)
    print(f"实验二: 均匀 {results['exp2']['uniform_params']} 参数 / 损失 {results['exp2']['uniform_final_loss']:.4f}")
    print(f"        分形 {results['exp2']['fractal_params']} 参数 / 损失 {results['exp2']['fractal_final_loss']:.4f}")
    print(f"实验三: 均匀最优深度 {results['exp3']['uniform_optimal_depth']} 层")
    print(f"        分形最优深度 {results['exp3']['fractal_optimal_depth']} 层")
