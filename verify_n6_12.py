#!/usr/bin/env python3
"""Independent cross-check of p2check (Erdos #64 power-of-2 cycles).
Method:
  - 4-cycle count via trace formula: c4 = (tr(A^4) - 2*sum(d^2) + 2m) / 8
    (derived from closed-walk decomposition of length-4 walks)
  - 8-cycle existence via brute force over all simple 8-tuples (itertools)
Usage: verify_n6_12.py  (checks cubic_*.g6 files)
"""
import sys
from itertools import product

BIAS6 = 63

def decode(line):
    n = ord(line[0]) - BIAS6
    total = n * (n - 1) // 2
    bits = []
    for c in line[1:]:
        v = ord(c) - BIAS6
        for b in range(5, -1, -1):
            bits.append((v >> b) & 1)
    adj = [[] for _ in range(n)]
    idx = 0
    for j in range(1, n):
        for i in range(j):
            if bits[idx]:
                adj[i].append(j)
                adj[j].append(i)
            idx += 1
    return n, adj

def matmul(B, C, n):
    return [[sum(B[i][k] * C[k][j] for k in range(n)) for j in range(n)] for i in range(n)]

def c4_trace(A, n, m):
    # c4 = (tr(A^4) - 2*sum(d^2) + 2m) / 8  (closed-walk decomposition)
    A2 = matmul(A, A, n)
    A4 = matmul(A2, A2, n)
    tr = sum(A4[i][i] for i in range(n))
    sd2 = sum(A2[i][j] for i in range(n) for j in range(n))  # = sum d_v^2
    return (tr - 2 * sd2 + 2 * m) // 8

def has8_bruteforce(adj, n):
    """Independent implementation: recursive DFS for a simple path of length 6
    in G-{s} from a neighbor a of s back to a (different) neighbor of s
    (that closes an 8-cycle)."""
    nbrset = [set(adj[v]) for v in range(n)]

    def dfs(cur, prev, d, used):
        if d == 6:
            return s in nbrset[cur]
        for w in adj[cur]:
            if w != prev and w != s and w not in used:
                used.add(w)
                if dfs(w, cur, d + 1, used):
                    return True
                used.discard(w)
        return False

    for s in range(n):
        for a in adj[s]:
            if a <= s:
                continue
            if dfs(a, s, 0, {s, a}):
                return True
    return False

def main():
    bad = 0
    for fname in sys.argv[1:]:
        nfile = fname.replace("cubic_", "").replace(".g6", "")
        exp_c4 = {}
        # parse C output
        c8c = {}
        c4c = {}
        for line in open(f"p2check_{nfile}.out"):
            if line.startswith("G") and line[1:].split(" ")[0].isdigit():
                parts = line.split()
                g = int(parts[0][1:])
                if "4C(" in parts[2]:
                    c4c[g] = int(parts[2][3:-1])
                elif "8C" in parts:
                    c8c[g] = True
                elif "16C" in parts:
                    c8c[g] = "16"
                elif "FREE" in parts:
                    c8c[g] = "FREE"
        gi = 0
        for line in open(fname):
            line = line.rstrip("\n")
            if not line:
                continue
            gi += 1
            n, adj = decode(line)
            if any(len(a) != 3 for a in adj):
                continue
            A = [[0] * n for _ in range(n)]
            for u in range(n):
                for v in adj[u]:
                    A[u][v] = 1
            c4 = c4_trace(A, n, 3 * n // 2)
            if c4 > 0:
                assert gi in c4c and c4c[gi] == c4, f"{fname} G{gi}: C says {c4c.get(gi)}, py says {c4}"
            else:
                has8 = has8_bruteforce(adj, n)
                if has8:
                    assert gi in c8c and c8c[gi] is True, f"{fname} G{gi}: expected 8C, C says {c8c.get(gi)}"
                else:
                    assert gi in c8c and c8c[gi] in ("16", "FREE"), f"{fname} G{gi}: expected 16C/FREE, C says {c8c.get(gi)}"
        print(f"{fname}: OK ({gi} graphs cross-verified)")
    print("ALL OK")

if __name__ == "__main__":
    main()
