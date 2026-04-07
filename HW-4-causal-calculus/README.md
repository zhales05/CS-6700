# HW 4 — Causal Calculus

## Back-Door Criterion

The **back-door criterion** (Pearl, 2009) identifies which variables you need to condition on to estimate a causal effect from observational data.

A set **Z** satisfies the back-door criterion relative to exposure **X** and outcome **Y** if:

1. **No node in Z is a descendant of X** — you don't condition on anything caused by the treatment.
2. **Z blocks every back-door path from X to Y** — a "back-door path" is any path from X to Y that starts with an arrow *into* X (i.e., non-causal paths that create spurious associations).

If you find such a Z, you can estimate the causal effect of X on Y by adjusting (conditioning) on Z — essentially removing confounding bias.

## Bayes-Ball Algorithm

The implementation uses the **Bayes-Ball algorithm** (Shachter, 1998) to test d-separation. The algorithm determines whether two nodes are conditionally independent given a conditioning set **Z** by simulating "ball" traversal through the graph.

A ball starts at node **X** and tries to reach node **Y**. At each intermediate node, the ball follows rules based on the node type and whether it is in **Z**:

| Path structure | Node in Z? | Ball passes? |
|---|---|---|
| **Chain** (→ m →) | No | Yes |
| **Chain** (→ m →) | Yes | No (blocked) |
| **Fork** (← m →) | No | Yes |
| **Fork** (← m →) | Yes | No (blocked) |
| **Collider** (→ m ←) | No | No (blocked) |
| **Collider** (→ m ←) | Yes, or a descendant of m is in Z | Yes |

If the ball cannot reach **Y** from **X**, then X and Y are **d-separated** given Z — meaning they are conditionally independent. The algorithm tracks traversal direction ("up" toward parents, "down" toward children) to distinguish chains, forks, and colliders at each node.

In this implementation, the algorithm is applied to the **manipulated graph** (all edges out of X removed) so that d-separation in that graph corresponds exactly to blocking all back-door paths.

## Usage

```bash
# Interactive mode (choose DAGitty paste or adjacency matrix input)
python dagitty.py

# Read a DAGitty file directly
python dagitty.py test.dagitty
```

The script parses the DAG, identifies exposure and outcome nodes, computes all valid adjustment sets satisfying the back-door criterion, and visualizes the graph.
