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
  python dagitty.py                    # interactive mode
  python dagitty.py graph.dagitty      # read DAGitty file directly
"""

import re
import sys
from itertools import chain, combinations

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


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


# ── DAGitty format parser ────────────────────────────────────────────────

def parse_dagitty(text):
    """Parse a DAGitty-format DAG string into (adj, names, exposure, outcome, positions).

    Supports node declarations with attributes like:
        NodeName [exposure,pos="-1.0,2.5"]
    and edge declarations like:
        A -> B
    """
    # Strip the outer dag { ... } wrapper
    text = text.strip()
    match = re.match(r'dag\s*\{(.*)\}\s*$', text, re.DOTALL)
    if match:
        text = match.group(1)

    nodes = {}       # name -> {exposure, outcome, pos}
    edges = []       # (src_name, dst_name)

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        # Edge line: may contain chained edges like A -> B -> C
        if '->' in line:
            # Strip any trailing attributes from the last node (rare but possible)
            parts = [p.strip() for p in line.split('->')]
            for i in range(len(parts) - 1):
                src = parts[i].split('[')[0].strip()
                dst = parts[i + 1].split('[')[0].strip()
                edges.append((src, dst))
                # Ensure edge nodes exist in the node dict
                for name in (src, dst):
                    if name not in nodes:
                        nodes[name] = {}
            continue

        # Node declaration line: NodeName [attrs]
        node_match = re.match(r'(\S+)\s*(?:\[([^\]]*)\])?\s*$', line)
        if node_match:
            name = node_match.group(1)
            attrs_str = node_match.group(2) or ""
            attrs = {}
            if 'exposure' in attrs_str:
                attrs['exposure'] = True
            if 'outcome' in attrs_str:
                attrs['outcome'] = True
            pos_match = re.search(r'pos="([^"]+)"', attrs_str)
            if pos_match:
                coords = pos_match.group(1).split(',')
                attrs['pos'] = (float(coords[0]), float(coords[1]))
            nodes[name] = attrs

    # Build ordered name list and adjacency matrix
    names = list(nodes.keys())
    idx = {name: i for i, name in enumerate(names)}
    n = len(names)
    adj = [[0] * n for _ in range(n)]
    for src, dst in edges:
        adj[idx[src]][idx[dst]] = 1

    # Find exposure and outcome
    exposure = None
    outcome = None
    for name, attrs in nodes.items():
        if attrs.get('exposure'):
            exposure = idx[name]
        if attrs.get('outcome'):
            outcome = idx[name]

    # Collect positions (if any)
    positions = {}
    for name, attrs in nodes.items():
        if 'pos' in attrs:
            positions[idx[name]] = attrs['pos']

    return adj, names, exposure, outcome, positions


# ── Input / Output ────────────────────────────────────────────────────────

def read_input():
    """Read graph from user — either DAGitty format or manual adjacency matrix."""
    print("=" * 55)
    print("  DAGitty Clone – Back-Door Criterion Adjustment Sets")
    print("=" * 55)
    print()
    print("Input format:")
    print("  1) DAGitty text format")
    print("  2) Manual (node names + adjacency matrix)")
    choice = input("> ").strip()
    print()

    if choice == "1":
        return read_dagitty_input()
    else:
        return read_manual_input()


def read_dagitty_input():
    """Read DAGitty format from stdin or prompt for paste."""
    print("Paste your DAGitty DAG below, then press Enter on an empty line:")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    text = "\n".join(lines)

    adj, names, exposure, outcome, positions = parse_dagitty(text)
    n = len(names)

    print(f"Parsed {n} nodes: {', '.join(names)}")
    print()
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

    if exposure is None:
        exposure_name = input("Enter the EXPOSURE (treatment) node: ").strip()
        if exposure_name not in names:
            print(f"Error: '{exposure_name}' is not a valid node name.")
            sys.exit(1)
        exposure = names.index(exposure_name)

    if outcome is None:
        outcome_name = input("Enter the OUTCOME node: ").strip()
        if outcome_name not in names:
            print(f"Error: '{outcome_name}' is not a valid node name.")
            sys.exit(1)
        outcome = names.index(outcome_name)

    print(f"  Exposure: {names[exposure]}")
    print(f"  Outcome:  {names[outcome]}")

    return adj, names, exposure, outcome, positions


def read_manual_input():
    """Read adjacency matrix and node info from the user."""
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
    exposure_name = input("Enter the EXPOSURE (treatment) node: ").strip()
    outcome_name = input("Enter the OUTCOME node: ").strip()

    if exposure_name not in names:
        print(f"Error: '{exposure_name}' is not a valid node name.")
        sys.exit(1)
    if outcome_name not in names:
        print(f"Error: '{outcome_name}' is not a valid node name.")
        sys.exit(1)

    exposure = names.index(exposure_name)
    outcome = names.index(outcome_name)

    return adj, names, exposure, outcome, None


def main():
    # If a file argument is given, read DAGitty format from it directly
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            text = f.read()
        adj, names, exposure, outcome, positions = parse_dagitty(text)
        n = len(names)
        print(f"Parsed {n} nodes from {sys.argv[1]}: {', '.join(names)}")
        if exposure is None:
            exposure_name = input("Enter the EXPOSURE (treatment) node: ").strip()
            exposure = names.index(exposure_name)
        if outcome is None:
            outcome_name = input("Enter the OUTCOME node: ").strip()
            outcome = names.index(outcome_name)
    else:
        adj, names, exposure, outcome, positions = read_input()

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

    # Show the graph
    visualize(adj, names, exposure, outcome, all_valid, positions)


def visualize(adj, names, exposure, outcome, adjustment_sets, positions=None):
    """Draw the DAG with color-coded nodes and display adjustment sets."""
    n = len(adj)
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    for i in range(n):
        for j in range(n):
            if adj[i][j] == 1:
                G.add_edge(i, j)

    # Pick the first minimal adjustment set for highlighting (if any)
    highlight = set()
    if adjustment_sets:
        mins = minimal_sets(adjustment_sets)
        highlight = mins[0]

    # Node colors
    node_colors = []
    for i in range(n):
        if i == exposure:
            node_colors.append("#4CAF50")   # green
        elif i == outcome:
            node_colors.append("#F44336")   # red
        elif i in highlight:
            node_colors.append("#2196F3")   # blue
        else:
            node_colors.append("#BDBDBD")   # grey

    labels = {i: names[i] for i in range(n)}

    # Use DAGitty positions if provided, otherwise fall back to layout algorithms
    if positions and len(positions) == n:
        # DAGitty uses y-axis inverted (negative = top), flip for matplotlib
        pos = {i: (positions[i][0], -positions[i][1]) for i in positions}
    else:
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
        except Exception:
            pos = nx.spring_layout(G, seed=42, k=2.0)

    fig, ax = plt.subplots(figsize=(8, 6))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800,
                           edgecolors="black", linewidths=1.5, ax=ax)
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold", ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color="#555555", arrows=True,
                           arrowsize=20, arrowstyle="-|>",
                           connectionstyle="arc3,rad=0.1", ax=ax)

    # Legend
    legend_handles = [
        mpatches.Patch(color="#4CAF50", label=f"Exposure ({names[exposure]})"),
        mpatches.Patch(color="#F44336", label=f"Outcome ({names[outcome]})"),
    ]
    if highlight:
        set_str = ", ".join(names[i] for i in sorted(highlight))
        legend_handles.append(mpatches.Patch(color="#2196F3",
                                             label=f"Adjust for {{ {set_str} }}"))
    legend_handles.append(mpatches.Patch(color="#BDBDBD", label="Other nodes"))
    ax.legend(handles=legend_handles, loc="upper left", fontsize=9)

    ax.set_title("Causal DAG — Back-Door Criterion", fontsize=13, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
