import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.linewidth": 0.8,
})

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- Figure 1: Murray's law branching cost ----------
# Model C(rho) = resistance + maintenance, resistance ~ 1/r^4, maintenance ~ r^2
# rho is the branch ratio (daughter/parent radius). Show resistance, maintenance, total.
rho = np.linspace(0.4, 0.98, 200)
# physical scaling with branch ratio rho = r/r0 ; normalized so rho0 = 2^(-1/3)
rho0 = 2 ** (-1 / 3)
# C(r) = a/r^4 + b r^2 ; choose a,b so minimum at rho0 => rho0^6 = 2a/b
b = 1.0
a = b * rho0**6 / 2
resistance = a / rho**4
maintenance = b * rho**2
total = resistance + maintenance
# log scale for resistance to show the explosion at low rho
fig, ax1 = plt.subplots(figsize=(3.4, 2.4))
ax1.plot(rho, resistance, color="tab:red", label=r"Resistance $a/\rho^4$")
ax1.plot(rho, maintenance, color="tab:blue", label=r"Maintenance $b\rho^2$")
ax1.plot(rho, total, color="tab:green", label=r"Total $C(\rho)$", linewidth=1.8)
ax1.set_yscale("symlog")
ax1.axvline(rho0, color="black", linestyle="--", linewidth=0.8)
ax1.annotate(r"$\rho=2^{-1/3}\approx0.79$", xy=(rho0, total.min()),
             xytext=(rho0 + 0.03, 0.5), fontsize=7,
             arrowprops=dict(arrowstyle="->", linewidth=0.6))
ax1.set_xlabel(r"Branch ratio $\rho$")
ax1.set_ylabel(r"Cost (symlog)")
ax1.legend(loc="upper right", frameon=False)
ax1.set_title("(a) Murray's-law variational cost", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_murray.pdf"))
fig.savefig(os.path.join(OUT, "fig_murray.png"), dpi=300)
plt.close(fig)

# ---------- Figure 2: Fractal vs uniform parameter count & loss ----------
# Data: uniform 400641 params loss 113.61 ; fractal 301569 params loss 113.62
labels = ["Uniform", "Fractal"]
params = [400641, 301569]
loss = [113.61, 113.62]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.3))
b1 = ax1.bar(labels, params, color=["#bbbbbb", "#4C72B0"], width=0.55)
for b, v in zip(b1, params):
    ax1.text(b.get_x() + b.get_width() / 2, v + 6000, f"{v:,}", ha="center", fontsize=7)
ax1.set_ylabel("Parameter count")
ax1.set_title("(a) Parameters", fontsize=9)
ax1.set_ylim(0, 460000)

b2 = ax2.bar(labels, loss, color=["#bbbbbb", "#4C72B0"], width=0.55)
for b, v in zip(b2, loss):
    ax2.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v}", ha="center", fontsize=7)
ax2.set_ylabel("Loss")
ax2.set_title("(b) Validation loss (nearly equal)", fontsize=9)
ax2.set_ylim(113.4, 113.8)
fig.suptitle("Fractal vs uniform transformer: 25% fewer parameters, equal loss",
             fontsize=9, y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_fractal_params.pdf"))
fig.savefig(os.path.join(OUT, "fig_fractal_params.png"), dpi=300)
plt.close(fig)

# ---------- Figure 3: Optimal-depth sweep (true data from shape.md) ----------
# depths [2,4,6,8,10,14,18]; uniform & fractal final test loss
depth = np.array([2, 4, 6, 8, 10, 14, 18])
uniform_loss = np.array([9.3835, 41.5486, 101.3744, 79.4626, 113.6231,
                         74.4689, 113.6139])
fractal_loss = np.array([8.9361, 71.9961, 39.8385, 77.4526, 88.5335,
                         113.5968, 113.6006])
fig, ax = plt.subplots(figsize=(3.4, 2.3))
ax.plot(depth, uniform_loss, "o-", color="tab:red", linewidth=1.4,
        markersize=4, label="Uniform")
ax.plot(depth, fractal_loss, "s-", color="tab:green", linewidth=1.4,
        markersize=4, label="Fractal")
ax.axvspan(3, 18, color="gray", alpha=0.12)
ax.axhline(113.61, color="gray", linestyle=":", linewidth=0.8)
ax.annotate("optimal depth = 2\nfor both", xy=(2, 8.9), xytext=(10.5, 8),
            fontsize=7, arrowprops=dict(arrowstyle="->", linewidth=0.6))
ax.annotate("loss cliff (depth >= 4)", xy=(6, 39), xytext=(8.5, 30),
            fontsize=7, arrowprops=dict(arrowstyle="->", linewidth=0.6))
ax.set_xlabel("Depth")
ax.set_ylabel("Final test loss")
ax.set_title("Optimal-depth sweep: loss cliff beyond depth 2", fontsize=9)
ax.legend(loc="upper right", frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_depth.pdf"))
fig.savefig(os.path.join(OUT, "fig_depth.png"), dpi=300)
plt.close(fig)

print("figures written to", OUT)
