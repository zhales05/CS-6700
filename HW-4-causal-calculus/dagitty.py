"""
Simple DAGitty Clone
====================
Generates a random DAG (up to 10 nodes), picks a random exposure and
outcome, and finds all valid adjustment sets satisfying the back-door
criterion.

The back-door criterion (Pearl, 2009):
  A set Z satisfies the back-door criterion relative to (X, Y) if:
    1. No node in Z is a descendant of X.
    2. Z blocks every back-door path from X to Y
       (i.e. X and Y are d-separated in the graph where all arrows
        out of X have been removed, given Z).

Usage:
  python dagitty.py
"""

import random
from itertools import combinations, chain


# ── Graph helpers (no external libraries) ─────────────────────────────────

def get_children(adj, node):
    """Return the set of children of *node* (node -> child)."""
    n = len(adj)
    return {j for j in range(n) if adj[node][j] == 1}


def get_parents(adj, node):
    """Return the set of parents of *node* (parent -> node)."""
    n = len(adj)
    return {j for j in range(n) if adj[j][node] == 1}


def get_descendants(adj, node):
    """BFS/DFS to find all descendants of *node*."""
    visited = set()
    stack = list(get_children(adj, node))
    while stack:
        cur = stack.pop()
        if cur not in visited:
            visited.add(cur)
            stack.extend(get_children(adj, cur) - visited)
    return visited


def get_ancestors(adj, node):
    """BFS/DFS to find all ancestors of *node*."""
    visited = set()
    stack = list(get_parents(adj, node))
    while stack:
        cur = stack.pop()
        if cur not in visited:
            visited.add(cur)
            stack.extend(get_parents(adj, cur) - visited)
    return visited


# ── D-separation via Bayes-Ball algorithm ─────────────────────────────────

def d_separated(adj, x, y, z):
    """Check whether node x and node y are d-separated given set z.

    Uses the 'reachable' approach: we find all nodes reachable from x
    by active paths given z, and check whether y is among them.

    An active path obeys these rules at each intermediate node m:
      - Chain    (→ m →) or fork (← m →): active iff m ∉ Z
      - Collider (→ m ←):                 active iff m ∈ Z or a descendant of m ∈ Z
    """
    n = len(adj)
    z = set(z)

    # Precompute: which nodes are in Z or have a descendant in Z
    # (needed for the collider rule)
    z_or_desc = set(z)
    for node in z:
        z_or_desc |= get_ancestors(adj, node)  # ancestors of z nodes
    # Actually we need: m is active as collider if m or any descendant of m is in Z
    # Equivalently: m is active as collider if m is an ancestor of some node in Z, or m is in Z
    ancestors_of_z = set()
    for node in z:
        ancestors_of_z |= get_ancestors(adj, node)
    collider_active = z | ancestors_of_z

    # BFS over (node, direction) pairs
    # direction: "up" means we arrived via a child->parent edge (going up)
    #            "down" means we arrived via a parent->child edge (going down)
    visited = set()
    queue = []

    # Start from x: we can leave x going up (to parents) or down (to children)
    for parent in get_parents(adj, x):
        queue.append((parent, "up"))
    for child in get_children(adj, x):
        queue.append((child, "down"))

    reachable = set()

    while queue:
        current, direction = queue.pop(0)
        if (current, direction) in visited:
            continue
        visited.add((current, direction))

        if current != x:
            reachable.add(current)

        # Determine what moves are allowed from (current, direction)
        if direction == "up":
            # We came up to 'current' (from a child).
            # current is a non-collider on paths through it if we continue
            # up or turn around and go down.
            if current not in z:
                # Non-collider, not conditioned on → path stays active
                # Continue going up (to current's parents)
                for parent in get_parents(adj, current):
                    queue.append((parent, "up"))
                # Turn around going down (to current's other children)
                for child in get_children(adj, current):
                    queue.append((child, "down"))
        else:
            # direction == "down": we came down to 'current' (from a parent).
            # Case 1: current is a non-collider for continuing down
            if current not in z:
                for child in get_children(adj, current):
                    queue.append((child, "down"))
            # Case 2: current is a collider (we came down, and could go up)
            # A collider is active if current ∈ collider_active
            if current in collider_active:
                for parent in get_parents(adj, current):
                    queue.append((parent, "up"))

    return y not in reachable


# ── Back-door criterion ───────────────────────────────────────────────────

def remove_edges_from(adj, node):
    """Return a copy of adj with all edges out of *node* removed."""
    n = len(adj)
    new_adj = [row[:] for row in adj]
    for j in range(n):
        new_adj[node][j] = 0
    return new_adj


def powerset(s):
    """All subsets of set s."""
    s = list(s)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def find_adjustment_sets(adj, exposure, outcome):
    """Find all valid adjustment sets satisfying the back-door criterion.

    Returns a list of sets.  Each set contains node indices.
    """
    n = len(adj)
    descendants_of_x = get_descendants(adj, exposure)

    # Candidates: all nodes except exposure, outcome, and descendants of exposure
    candidates = set(range(n)) - {exposure, outcome} - descendants_of_x

    # Manipulated graph: remove all edges out of exposure
    adj_manip = remove_edges_from(adj, exposure)

    valid = []
    for z in powerset(candidates):
        z_set = set(z)
        if d_separated(adj_manip, exposure, outcome, z_set):
            valid.append(z_set)

    return valid


def minimal_sets(sets):
    """Keep only minimal sets (no proper subset is also in the list)."""
    sets = sorted(sets, key=len)
    minimal = []
    for s in sets:
        if not any(prev < s for prev in minimal):  # prev is strict subset
            minimal.append(s)
    return minimal


# ── Input / Output ────────────────────────────────────────────────────────

def read_input():
    """Read adjacency matrix and node info from the user."""
    print("=" * 55)
    print("  DAGitty Clone – Back-Door Criterion Adjustment Sets")
    print("=" * 55)
    print()

    # Node names
    raw = input("Enter node names separated by commas:\n> ").strip()
    names = [s.strip() for s in raw.split(",")]
    n = len(names)
    print(f"\nYou have {n} nodes: {names}\n")

    # Adjacency matrix
    print(f"Enter the {n}x{n} adjacency matrix row by row.")
    print("(1 = edge from row-node to col-node, 0 = no edge)")
    print(f"Column order: {names}\n")

    adj = []
    for i in range(n):
        while True:
            row_str = input(f"  Row {i} ({names[i]}): ").strip()
            vals = row_str.replace(",", " ").split()
            if len(vals) == n and all(v in ("0", "1") for v in vals):
                adj.append([int(v) for v in vals])
                break
            print(f"  ⚠ Please enter exactly {n} values (0 or 1).")

    print()

    # Print the graph for confirmation
    print("Graph edges:")
    edge_count = 0
    for i in range(n):
        for j in range(n):
            if adj[i][j] == 1:
                print(f"  {names[i]} → {names[j]}")
                edge_count += 1
    if edge_count == 0:
        print("  (none)")
    print()

    # Exposure and outcome
    exposure_name = input(f"Enter the EXPOSURE (treatment) node: ").strip()
    outcome_name = input(f"Enter the OUTCOME node: ").strip()

    if exposure_name not in names:
        print(f"Error: '{exposure_name}' is not a valid node name.")
        sys.exit(1)
    if outcome_name not in names:
        print(f"Error: '{outcome_name}' is not a valid node name.")
        sys.exit(1)

    exposure = names.index(exposure_name)
    outcome = names.index(outcome_name)

    return adj, names, exposure, outcome


def main():
    import sys

    adj, names, exposure, outcome = read_input()

    print()
    print("-" * 55)
    print(f"  Exposure: {names[exposure]}")
    print(f"  Outcome:  {names[outcome]}")
    print("-" * 55)

    # Find all valid adjustment sets
    all_valid = find_adjustment_sets(adj, exposure, outcome)

    if not all_valid:
        print("\n✗ No valid adjustment set exists.")
        print("  The causal effect may not be identifiable via the back-door criterion.")
    else:
        # Show minimal sets
        mins = minimal_sets(all_valid)

        print(f"\nAll valid adjustment sets ({len(all_valid)} total):\n")
        for z in sorted(all_valid, key=lambda s: (len(s), sorted(s))):
            if len(z) == 0:
                print("  { }  (empty set — no conditioning needed)")
            else:
                print(f"  {{ {', '.join(names[i] for i in sorted(z))} }}")

        print(f"\nMinimal adjustment sets ({len(mins)}):\n")
        for z in mins:
            if len(z) == 0:
                print("  { }  (empty set — no conditioning needed)")
            else:
                print(f"  {{ {', '.join(names[i] for i in sorted(z))} }}")

    print()


if __name__ == "__main__":
    main()
