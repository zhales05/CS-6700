import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_sierpinski(size=2048, depth=10):
    """Generate a Sierpinski triangle as a boolean numpy array using recursive subdivision."""
    img = np.zeros((size, size), dtype=bool)

    def fill_triangle(x0, y0, x1, y1, x2, y2):
        """Fill a triangle defined by three vertices."""
        from matplotlib.path import Path
        xs = np.arange(min(x0, x1, x2), max(x0, x1, x2) + 1)
        ys = np.arange(min(y0, y1, y2), max(y0, y1, y2) + 1)
        if len(xs) == 0 or len(ys) == 0:
            return
        xx, yy = np.meshgrid(xs, ys)
        points = np.column_stack([xx.ravel(), yy.ravel()])
        path = Path([(x0, y0), (x1, y1), (x2, y2), (x0, y0)])
        mask = path.contains_points(points).reshape(yy.shape)
        img[yy[mask], xx[mask]] = True

    def sierpinski(x0, y0, x1, y1, x2, y2, d):
        if d == 0:
            fill_triangle(x0, y0, x1, y1, x2, y2)
            return
        # Midpoints
        mx01 = (x0 + x1) // 2
        my01 = (y0 + y1) // 2
        mx12 = (x1 + x2) // 2
        my12 = (y1 + y2) // 2
        mx02 = (x0 + x2) // 2
        my02 = (y0 + y2) // 2
        # Three sub-triangles (skip the middle one)
        sierpinski(x0, y0, mx01, my01, mx02, my02, d - 1)
        sierpinski(mx01, my01, x1, y1, mx12, my12, d - 1)
        sierpinski(mx02, my02, mx12, my12, x2, y2, d - 1)

    margin = 10
    sierpinski(
        size // 2, margin,           # top vertex
        margin, size - margin,       # bottom-left
        size - margin, size - margin, # bottom-right
        depth,
    )
    return img


def box_count(Z, box_size):
    """Count boxes of given size that contain at least one pixel of the fractal."""
    S = Z.shape[0]
    # Trim to multiple of box_size
    S_trim = (S // box_size) * box_size
    Z_trim = Z[:S_trim, :S_trim]
    positions = np.arange(0, S_trim, box_size)
    H = np.add.reduceat(Z_trim.astype(int), positions, axis=0)
    H = np.add.reduceat(H, positions, axis=1)
    return np.count_nonzero(H)


def estimate_fractal_dimension(image):
    """Estimate fractal dimension using box-counting across multiple scales."""
    size = image.shape[0]
    box_sizes = [2**i for i in range(1, int(np.log2(size)) - 1)]
    counts = [box_count(image, bs) for bs in box_sizes]

    log_inv_sizes = np.log(1.0 / np.array(box_sizes))
    log_counts = np.log(np.array(counts))

    # Linear fit
    coeffs = np.polyfit(log_inv_sizes, log_counts, 1)
    dimension = coeffs[0]
    return dimension, log_inv_sizes, log_counts, coeffs


def plot_results(log_inv_sizes, log_counts, dimension, coeffs):
    """Create log-log plot of box-counting results with linear fit."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(log_inv_sizes, log_counts, color="steelblue", zorder=5, label="Data")

    fit_line = np.polyval(coeffs, log_inv_sizes)
    ax.plot(log_inv_sizes, fit_line, color="tomato", linewidth=2,
            label=f"Linear fit (slope = {dimension:.4f})")

    theoretical = np.log(3) / np.log(2)
    ax.set_xlabel("log(1 / box size)")
    ax.set_ylabel("log(count)")
    ax.set_title("Box-Counting Fractal Dimension of Sierpinski Triangle")
    ax.legend()
    ax.text(0.05, 0.92,
            f"Estimated dim: {dimension:.4f}\nTheoretical dim: {theoretical:.4f}",
            transform=ax.transAxes, fontsize=11,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "box_counting_plot.png"), dpi=150)
    plt.close()


def main():
    print("Generating Sierpinski triangle...")
    image = generate_sierpinski(2048, 10)

    # Save fractal image
    img_path = os.path.join(OUTPUT_DIR, "sierpinski.png")
    plt.imsave(img_path, image, cmap="binary_r")
    print(f"Saved fractal image to {img_path}")

    print("Estimating fractal dimension via box-counting...")
    dimension, log_inv_sizes, log_counts, coeffs = estimate_fractal_dimension(image)

    theoretical = np.log(3) / np.log(2)
    print(f"Estimated fractal dimension: {dimension:.4f}")
    print(f"Theoretical fractal dimension: {theoretical:.4f}")
    print(f"Error: {abs(dimension - theoretical):.4f}")

    plot_results(log_inv_sizes, log_counts, dimension, coeffs)
    print(f"Saved box-counting plot to {os.path.join(OUTPUT_DIR, 'box_counting_plot.png')}")


if __name__ == "__main__":
    main()
