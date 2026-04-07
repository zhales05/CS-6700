# HW-5: Fractal Dimensions

## Part 1: Empirical Fractal Dimension Estimation

I generated a Sierpinski triangle (2048x2048, depth 10) and estimated its fractal dimension using the **box-counting method**.

The idea is straightforward: overlay the image with a grid of square boxes of side length $\epsilon$, and count how many boxes $N(\epsilon)$ contain at least one pixel of the fractal. For a fractal, the relationship is:

$$N(\epsilon) \sim \epsilon^{-D}$$

where $D$ is the fractal (box-counting) dimension. Taking logarithms:

$$\log N(\epsilon) = -D \log \epsilon + C$$

So the slope of $\log N$ vs. $\log(1/\epsilon)$ gives the fractal dimension.

I computed box counts at box sizes $\epsilon = 2, 4, 8, \dots, 512$ and performed a linear regression on the log-log data.

**Results:**
- Estimated fractal dimension: **1.5771**
- Theoretical fractal dimension: $\log 3 / \log 2 \approx 1.5850$
- Error: 0.0078

The estimate is within 0.5% of the theoretical value. See `box_counting_plot.png` for the log-log regression and `sierpinski.png` for the generated fractal.

---

## Part 2: Hausdorff Dimension

The **Hausdorff dimension** of a set $S$ in a metric space is defined as:

$$\dim_H(S) = \inf \{ d \geq 0 : \mathcal{H}^d(S) = 0 \}$$

where $\mathcal{H}^d(S)$ is the $d$-dimensional Hausdorff measure of $S$ (defined below).

Equivalently, it is the critical exponent at which the Hausdorff measure transitions from infinity to zero:
- For $d < \dim_H(S)$, we have $\mathcal{H}^d(S) = \infty$.
- For $d > \dim_H(S)$, we have $\mathcal{H}^d(S) = 0$.

**In my own words:** Imagine trying to measure a set using a "$d$-dimensional ruler." If $d$ is too small (say, measuring a surface with a length ruler), you get infinity — the set is too big for that notion of size. If $d$ is too large (measuring a curve with an area ruler), you get zero — the set is too thin. The Hausdorff dimension is the exact threshold where the measurement flips from infinite to zero. For ordinary shapes (lines, surfaces, volumes), this recovers the familiar integer dimensions 1, 2, 3. But for fractals, this threshold can land on a non-integer value, capturing the idea that the set is "more than a line but less than a surface," for example.

---

## Part 3: Hausdorff Measure

The **$d$-dimensional Hausdorff measure** of a set $S$ is constructed in two steps.

**Step 1 — Approximate measure at scale $\delta$:**

$$\mathcal{H}^d_\delta(S) = \inf \left\{ \sum_{i=1}^{\infty} |U_i|^d \;\middle|\; S \subseteq \bigcup_{i=1}^{\infty} U_i, \; |U_i| \leq \delta \right\}$$

Here, $\{U_i\}$ is a countable cover of $S$ by sets of diameter at most $\delta$, and $|U_i|$ denotes the diameter of $U_i$. We take the infimum over all such covers.

**Step 2 — Take the limit as $\delta \to 0$:**

$$\mathcal{H}^d(S) = \lim_{\delta \to 0} \mathcal{H}^d_\delta(S)$$

This limit exists (possibly as $\infty$) because $\mathcal{H}^d_\delta(S)$ is non-decreasing as $\delta$ decreases (smaller $\delta$ means fewer admissible covers, so the infimum can only increase).

**In my own words:** To compute the Hausdorff measure, you cover the set with small pieces (balls, cubes, arbitrary sets) each no larger than some diameter $\delta$. For each piece, you compute $(\text{diameter})^d$ and sum these up across the entire cover. You then find the most efficient cover — the one that minimizes this sum. Finally, you let $\delta$ shrink to zero, forcing the cover pieces to become arbitrarily fine. The resulting value is the $d$-dimensional Hausdorff measure. When $d = 1$, this generalizes the concept of length; when $d = 2$, area; when $d = 3$, volume. The power of the Hausdorff measure is that $d$ can be any non-negative real number, allowing us to assign meaningful "size" to fractal sets that have no well-defined length, area, or volume.
