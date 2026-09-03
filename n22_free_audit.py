# -*- coding: utf-8 -*-
"""Independent audit of FREE graphs reported by p2check (Erdős #64).
For every graph labeled FREE in the p2check output:
  1) recount 4-cycles by trace formula  c4 = (tr A^4 - 2*sd2 + 2m)/8
     (sd2 = sum of ALL A^2 entries)
  2) recount 8-cycles by independent recursive DFS (simple path of L-2 edges
     in G-{s} from one neighbor of s to a different neighbor of s;
     each cycle counted 2L times => divide by 2L)
  3) same for 16-cycles
  4) final sanity net: enumerate ALL simple cycle lengths and assert none of
     {4, 8, 16} occurs.
Exit 0 with 'AUDIT OK' iff all FREE labels are independently confirmed.
Usage: python3 n22_free_audit.py p2check_22.out
"""
import re, sys

def matmul(A, B):
    n = len(A)
    C = [[0]*n for _ in range(n)]
    for i in range(n):
        Ci = C[i]; Ai = A[i]
        for k in range(n):
            if Ai[k]:
                Aik = Ai[k]; Bk = B[k]
                for j in range(n):
                    Ci[j] += Aik * Bk[j]
    return C

def count4_adj(A, m):
    n = len(A)
    A2 = matmul(A, A)
    A4 = matmul(A2, A2)
    trA4 = sum(A4[i][i] for i in range(n))
    sd2 = sum(sum(row) for row in A2)          # 1^T A^2 1, NOT tr(A^2)
    return (trA4 - 2*sd2 + 2*m) // 8

def adj_from_lines(lines):
    n = 0
    adj = {}
    for ln in lines:
        v, rest = ln.split(":")
        v = int(v.strip())
        n = max(n, v)
        adj[v] = [int(x) for x in rest.split()]
    return {v: adj[v] for v in range(1, n+1)}, n

def count_cycles_len(n, adj, L):
    """# simple cycles of length L via neighbor-of-s paths in G-{s}."""
    if n < L:
        return 0
    total = 0
    for s in range(1, n+1):
        nbrs = adj[s]
        if len(nbrs) < 2:
            continue
        blocked = {s}
        for start in nbrs:
            used = {start}
            def dfs(u, d):
                nonlocal total
                if d == L - 2:
                    if u in nbrs and u != start:
                        total += 1
                    return
                for w in adj[u]:
                    if w not in blocked and w not in used:
                        used.add(w)
                        dfs(w, d+1)
                        used.discard(w)
            dfs(start, 0)
    assert total % (2*L) == 0, f"path count {total} not divisible by {2*L}"
    return total // (2*L)

def all_cycle_lengths(n, adj):
    lengths = set()
    for s in range(1, n+1):
        blocked = {s}
        def dfs(u, d, visited):
            for w in adj[u]:
                if w == s:
                    if d + 1 >= 3:
                        lengths.add(d + 1)
                elif w > s and w not in visited and d < n - 1:
                    dfs(w, d + 1, visited | {w})
        dfs(s, 0, {s})
    return lengths

def parse_free(path):
    """Parse p2check OUTPUT format:
       'G00001 n=10 4C(3)' / '... 8C' / '... 16C' / '... FREE' (+ adjacency for FREE)
    """
    graphs = []
    cur = None
    hdr = re.compile(r"^G(\d+) n=(\d+) (\S+?)(?:\((\d+)\))?\s*$")
    adjln = re.compile(r"^\s*\d+:")
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            m = hdr.match(line)
            if m:
                cur = {"no": int(m.group(1)), "n": int(m.group(2)),
                       "e": 3 * int(m.group(2)) // 2, "label": m.group(3), "adj": []}
                graphs.append(cur)
                continue
            if line.startswith("=="):
                cur = None
                continue
            if cur is not None and cur["label"] == "FREE" and adjln.match(line):
                cur["adj"].append(line)
    return [g for g in graphs if g["label"] == "FREE"]

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "p2check_22.out"
    free = parse_free(path)
    print(f"FREE graphs in {path}: {len(free)}")
    if not free:
        print("nothing to audit (no FREE graphs) — AUDIT OK")
        return
    bad = 0
    for g in free:
        n = g["n"]; m = g["e"]
        adj, n2 = adj_from_lines(g["adj"])
        assert n2 == n, f"graph {g['no']}: n mismatch {n2} vs {n}"
        assert len(g["adj"]) == n, f"graph {g['no']}: only {len(g['adj'])}/{n} adjacency lines"
        A = [[0]*(n+1) for _ in range(n+1)]
        for u in range(1, n+1):
            for v in adj[u]:
                A[u][v] = A[v][u] = 1
        c4 = count4_adj(A, m)
        c8 = count_cycles_len(n, adj, 8)
        c16 = count_cycles_len(n, adj, 16)
        cl = all_cycle_lengths(n, adj)
        pw2 = cl & {4, 8, 16, 32}
        ok = (c4 == 0 and c8 == 0 and c16 == 0 and not pw2)
        if not ok:
            bad += 1
        print(f"  graph {g['no']}: n={n} e={m}  c4={c4} c8={c8} c16={c16}  "
              f"cycle_lengths={sorted(cl)}  {'OK' if ok else '*** MISMATCH ***'}")
    if bad:
        print(f"*** {bad} MISMATCHES ***")
        sys.exit(1)
    print(f"AUDIT OK — all {len(free)} FREE labels independently confirmed")

if __name__ == "__main__":
    main()
