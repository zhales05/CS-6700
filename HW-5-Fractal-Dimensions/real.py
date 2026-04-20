from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os


img = Image.open("data/lightning.webp")

THRESHOLD = 50

# make the image either dark or light per pixel, based on the threshold
def binarize(image, threshold):
    gray = image.convert("L")
    return gray.point(lambda p: 255 if p > threshold else 0, "1")

# smallest power of 2 that is >= n
def next_power_of_2(n):
    return 1 << (n - 1).bit_length()

# pad a 2D bool array with False up to (next_pow2(H), next_pow2(W))
def pad_to_power_of_2(arr):
    H, W = arr.shape
    Ht = next_power_of_2(H)
    Wt = next_power_of_2(W)
    padded = np.zeros((Ht, Wt), dtype=bool)
    padded[:H, :W] = arr
    return padded

# count the number of boxes by box_size that contain at least one True value in the 2D boolean array
def count_boxes(arr, box_size):
    H, W = arr.shape
    rows, cols = H // box_size, W // box_size
    occupied = np.zeros((rows, cols), dtype=bool)
    
    for i in range(rows):
        for j in range(cols):
            box = arr[i*box_size:(i+1)*box_size, j*box_size:(j+1)*box_size]
            occupied[i, j] = np.any(box)  # True if at least one pixel in the box is True
            
    N = occupied.sum()            
    return N, occupied

def main():
    binary = binarize(img, THRESHOLD)
    binary.show()

    arr = np.array(binary, dtype=bool)   # NumPy 2D array, shape (H, W), dtype=bool
    padded = pad_to_power_of_2(arr)

    assert padded.sum() == arr.sum(), "padding changed the True-pixel count"
    print(f"original: {arr.shape}  true_pixels={arr.sum()}")
    print(f"padded:   {padded.shape}  true_pixels={padded.sum()}")

    sizes = [s for s in [2, 4, 8, 16, 32, 64, 128, 256] if s <= min(padded.shape) // 2]
    Ns = []
    for s in sizes:
        N, _ = count_boxes(padded, s)
        Ns.append(N)
        print(f"s={s:4d}  N={N}")

    sizes_arr = np.array(sizes)
    Ns_arr = np.array(Ns)

    x = np.log(1 / sizes_arr)
    y = np.log(Ns_arr)

    slope, intercept = np.polyfit(x, y, 1)
    dimension = slope
    print(f"\nFractal dimension D ≈ {dimension:.3f}")

    os.makedirs("plots", exist_ok=True)

    _, ax = plt.subplots()
    ax.scatter(x, y, label="box counts")
    ax.plot(x, slope * x + intercept, "r--", label=f"fit: D ≈ {dimension:.3f}")
    ax.set_xlabel("log(1/s)")
    ax.set_ylabel("log(N)")
    ax.set_title("Box-counting dimension of lightning")
    ax.legend()
    plt.savefig("plots/loglog.png", dpi=150)
    plt.close()
    print("saved plots/loglog.png")

if __name__ == "__main__":
    main()