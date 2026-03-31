import numpy as np
import matplotlib.pyplot as plt
from scipy.special import gamma


def volume_n_ball(n, r=1):
    """Volume of an n-dimensional ball of radius r."""
    return (np.pi ** (n / 2) / gamma(n / 2 + 1)) * r**n


def volume_n_cube(n, side=2):
    """Volume of an n-dimensional cube with given side length."""
    return side**n


# Sphere inscribed in cube: cube side=2, sphere radius=1
dims = np.arange(1, 51)
ratios = [volume_n_ball(n) / volume_n_cube(n) for n in dims]

plt.figure(figsize=(8, 5))
plt.plot(dims, ratios, "o-", markersize=4)
plt.xlabel("Dimension (n)")
plt.ylabel("V(ball) / V(cube)")
plt.title("Ratio of Inscribed Sphere to Cube Volume vs. Dimension")
plt.ylim(bottom=0)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("HW-3-Concentration-of-Measure/sphere_in_cube.png", dpi=150)
plt.close()

# Volume in the thin shell: fraction of volume between radius (1-eps) and 1
# V(shell) / V(ball) = 1 - (1-eps)^n since V(r) is proportional to r^n
dims2 = np.arange(1, 101)
epsilons = [0.01, 0.05, 0.1]

plt.figure(figsize=(8, 5))
for eps in epsilons:
    shell_fraction = 1 - (1 - eps) ** dims2
    plt.plot(dims2, shell_fraction, "o-", markersize=3, label=f"ε = {eps}")
plt.xlabel("Dimension (n)")
plt.ylabel("Fraction of Volume in Shell")
plt.title("Volume Concentrated in Thin Shell Near Surface of n-Ball")
plt.ylim(0, 1.05)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("HW-3-Concentration-of-Measure/volume_in_shell.png", dpi=150)
plt.close()

# The race between pi^(n/2) and Gamma(n/2 + 1)
dims3 = np.arange(1, 51)
numerator = np.pi ** (dims3 / 2)
denominator = np.array([gamma(n / 2 + 1) for n in dims3])
volumes = numerator / denominator

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.semilogy(dims3, numerator, "o-", markersize=4, label=r"$\pi^{n/2}$ (numerator)")
ax1.semilogy(dims3, denominator, "s-", markersize=4, label=r"$\Gamma(n/2+1)$ (denominator)")
ax1.set_xlabel("Dimension (n)")
ax1.set_ylabel("Value (log scale)")
ax1.set_title(r"The Race: $\pi^{n/2}$ vs $\Gamma(n/2+1)$")
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(dims3, volumes, "o-", markersize=4, color="tab:green")
ax2.set_xlabel("Dimension (n)")
ax2.set_ylabel("Volume of Unit Ball")
ax2.set_title(r"Volume $= \pi^{n/2} / \Gamma(n/2+1)$")
ax2.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig("HW-3-Concentration-of-Measure/numerator_denominator_race.png", dpi=150)
plt.close()

# --- Gaussian norm concentration: ||X||/sqrt(n) -> 1 as n grows ---
# Sample random Gaussian vectors and show their norms concentrate around sqrt(n)
np.random.seed(42)
n_samples = 5000
test_dims = [2, 10, 50, 200, 1000]

fig, axes = plt.subplots(1, len(test_dims), figsize=(18, 4), sharey=True)
for ax, n in zip(axes, test_dims):
    X = np.random.randn(n_samples, n)
    norms = np.linalg.norm(X, axis=1) / np.sqrt(n)
    ax.hist(norms, bins=50, density=True, alpha=0.7, color="steelblue", edgecolor="white")
    ax.axvline(1.0, color="red", lw=2, ls="--", label="1.0")
    ax.set_title(f"n = {n}")
    ax.set_xlim(0.5, 1.5)
    ax.set_xlabel(r"$\|X\| / \sqrt{n}$")
    if n == 2:
        ax.set_ylabel("Density")
axes[-1].legend()
fig.suptitle(
    r"Concentration of $\|X\|/\sqrt{n}$ for $X \sim \mathcal{N}(0, I_n)$",
    fontsize=14, y=1.02,
)
fig.tight_layout()
fig.savefig("HW-3-Concentration-of-Measure/gaussian_norm_concentration.png", dpi=150, bbox_inches="tight")
plt.close()

# --- Random projections: dot product of two random unit vectors -> 0 ---
n_samples = 10000
test_dims2 = [2, 10, 50, 500]

fig, axes = plt.subplots(1, len(test_dims2), figsize=(16, 4), sharey=True)
for ax, n in zip(axes, test_dims2):
    U = np.random.randn(n_samples, n)
    V = np.random.randn(n_samples, n)
    U = U / np.linalg.norm(U, axis=1, keepdims=True)
    V = V / np.linalg.norm(V, axis=1, keepdims=True)
    dots = np.sum(U * V, axis=1)
    ax.hist(dots, bins=60, density=True, alpha=0.7, color="coral", edgecolor="white")
    ax.axvline(0, color="black", lw=1.5, ls="--")
    ax.set_title(f"n = {n}")
    ax.set_xlim(-1, 1)
    ax.set_xlabel(r"$\langle u, v \rangle$")
    if n == 2:
        ax.set_ylabel("Density")
fig.suptitle(
    "Inner Product of Random Unit Vectors Concentrates at 0",
    fontsize=14, y=1.02,
)
fig.tight_layout()
fig.savefig("HW-3-Concentration-of-Measure/random_inner_products.png", dpi=150, bbox_inches="tight")
plt.close()

print("All plots saved.")
