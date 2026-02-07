import matplotlib.pyplot as plt
from math import gcd


def find_points(p, a, b):
    points = [None]
    for x in range(p):
        for y in range(p):
            if (y**2) % p == (x**3 + a*x + b) % p:
                points.append((x, y))
    return points

def plot_points(points):
    actual_points = [p for p in points if p is not None]
    xs = [point[0] for point in actual_points]
    ys = [point[1] for point in actual_points]

    plt.scatter(xs, ys, s=10)
    plt.title(f"Elliptic Curve y² = x³ + {a}x + {b} over F_{p}")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.show()
    
def point_add(P1, P2, p, a):
    # Point at infinity cases
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    
    x1, y1 = P1
    x2, y2 = P2
    
    # Case 2: P1 and P2 have same x but opposite y
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    
    # Case 3: Doubling a point where y = 0
    if P1 == P2 and y1 == 0:
        return None
    
    # Calculate slope
    if P1 == P2:  # Case 4: Point doubling
        m = (3 * x1**2 + a) * mod_inverse(2 * y1, p) % p
    else:  # Case 1: Adding different points
        m = (y2 - y1) * mod_inverse(x2 - x1, p) % p
        
    # Calculate new point
    x3 = (m**2 - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    
    return (x3, y3)
        
def mod_inverse(a, m):
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y
    
    _, x, _ = extended_gcd(a % m, m)
    return (x % m + m) % m

def point_order(P, p, a, group_size):
    if P is None:
        return 1
    
    current = P
    order = 1
    
    while True:
        current = point_add(current, P, p, a)
        order += 1
        if current is None:  # Reached point at infinity
            break
        if order > group_size:
            break
    
    return order 
        
def find_generator(points, p, a):
    group_size = len(points)
    print(f"Group has {group_size} points")
    
    for i, P in enumerate(points[1:], 1):
        order = point_order(P, p, a, group_size)
        print(f"Point {P} has order {order}")
        
        if order == group_size:
            print(f"\n*** Generator found: {P} ***")
            return P
    
    print("No generator found")
    return None

def discrete_log_mod_n(g, h, n):
    d = gcd(g, n)
    if h % d != 0:
        return None  # No solution
    # Reduce: k * (g/d) ≡ (h/d) (mod n/d)
    g, h, n = g // d, h // d, n // d
    k = (h * mod_inverse(g, n)) % n
    return k
    
p = 109
a = 1
b = 1    

# Question 1
points = find_points(p, a, b)
print(f"Total points found: {len(points)}")
# plot_points(points)

# Question 2
generator = find_generator(points, p, a)

# Question 4
g, h, n = 7, 53, 109
k = discrete_log_mod_n(g, h, n)
print(f"Discrete log: {k} * {g} ≡ {h} (mod {n})")
print(f"Verification: {k * g % 109}")  