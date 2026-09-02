"""Erdos-Gyarfas gadget search.
Find a cubic graph K and vertices a,b such that:
  (a) every cycle length of K is not in {4,8,16,32,...}  (powers of 2)
  (b) every simple a-b path length in K is not in {2,6,14,30,...} (powers of 2 minus 2)
Then G = K + two leaves t1,t2 attached to a,b gives an edge-gadget, and
H = internally cubic tree + gadget at each leaf is a CUBIC graph with no
cycle whose length is a power of 2  -> counterexample to Erdos-Gyarfas.
"""
import sys
from itertools import combinations

def gen_cubic(n):
    """Generate all simple cubic graphs on n vertices (vertices 0..n-1).
    Canonical order: always connect the lowest-index vertex with deg<3
    to higher-index vertices with deg<3.  Each graph may appear several
    times (duplicates removed by caller)."""
    deg = [0]*n
    edges = []
    def rec():
        # find lowest vertex with deg<3
        v = -1
        for i in range(n):
            if deg[i] < 3:
                v = i; break
        if v == -1:
            yield tuple(sorted(edges))
            return
        # candidates: higher index, deg<3, not adjacent
        cand = [u for u in range(v+1, n) if deg[u] < 3 and (v,u) not in edges]
        # if v has already 2 edges, next partner must complete degree 3 -> but pairs:
        need = 3 - deg[v]
        for combo in combinations(cand, need):
            # avoid adding edges that would force later vertex to exceed 3 with only high
            for u in combo:
                deg[v] += 1; deg[u] += 1
                edges.append((v,u))
            # prune: any vertex that can no longer reach 3?  count free slots
            ok = True
            free = [3 - deg[i] for i in range(n)]
            if sum(free) % 2 != 0:
                ok = False
            if ok:
                yield from rec()
            # restore
            for u in combo:
                deg[v] -= 1; deg[u] -= 1
                edges.pop()
    seen = set()
    out = []
    for e in rec():
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out

def rebuild(n, edges):
    adj = [[] for _ in range(n)]
    for u,v in edges:
        adj[u].append(v); adj[v].append(u)
    return adj

def cycle_lengths(adj):
    """All lengths of simple cycles (as set)."""
    n = len(adj)
    res = set()
    for s in range(n):
        # enumerate simple paths starting at s with all internal > s (each cycle once)
        visited = {s}
        stack = [(s, [s])]
        # DFS iterative: path from s
        def dfs(u, path, visited):
            for w in adj[u]:
                if w == s and len(path) >= 3:
                    res.add(len(path))
                elif w not in visited and w > s or (w < s):  # allow all, cycles counted multiple times
                    pass
        # simpler: recursive
        def rec(u, path):
            for w in adj[u]:
                if w == s and len(path) >= 3:
                    res.add(len(path))
                elif w not in visited and w > s:
                    visited.add(w); path.append(w)
                    rec(w, path)
                    path.pop(); visited.discard(w)
        rec(s, [s])
    return res

def path_lengths_between(adj, a, b):
    """All lengths of simple a-b paths."""
    n = len(adj)
    res = set()
    visited = {a}
    def rec(u, dist):
        for w in adj[u]:
            if w == b:
                res.add(dist+1)
            elif w not in visited:
                visited.add(w)
                rec(w, dist+1)
                visited.discard(w)
    rec(a, 0)
    return res

POW2 = {4, 8, 16, 32, 64, 128}

def check(n, edges, verbose=False):
    adj = rebuild(n, edges)
    cl = cycle_lengths(adj)
    if cl & POW2:
        return None
    for a in range(n):
        for b in range(a+1, n):
            pl = path_lengths_between(adj, a, b)
            if pl & {p-2 for p in POW2}:
                continue
            return (a, b, cl, pl)
    return None

def main():
    for n in range(10, 21, 2):
        print(f"--- cubic graphs on {n} vertices ---", flush=True)
        cnt = 0
        for edges in gen_cubic(n):
            cnt += 1
            r = check(n, edges)
            if r:
                a, b, cl, pl = r
                print(f"!!! FOUND n={n} a={a} b={b}")
                print(f"    cycles: {sorted(cl)}")
                print(f"    a-b paths: {sorted(pl)}")
                print(f"    edges: {sorted(edges)}")
                return
        print(f"    ({cnt} graphs checked, nothing)", flush=True)
    print("NO GADGET FOUND")

if __name__ == "__main__":
    main()
