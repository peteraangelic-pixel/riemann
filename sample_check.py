#!/usr/bin/env python3
"""Sample cross-check for n=14..20: take graphs the C checker labeled 8C or
16C/FREE (i.e. 4-cycle-free) and re-verify with independent Python DFS."""
import random, sys
sys.setrecursionlimit(10000)
BIAS6 = 63
def decode(line):
    n = ord(line[0]) - BIAS6
    total = n*(n-1)//2
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
                adj[i].append(j); adj[j].append(i)
            idx += 1
    return n, adj
def has8(adj, n):
    nbr = [set(a) for a in adj]
    def dfs(cur, prev, d, s, used):
        if d == 6:
            return s in nbr[cur]
        for w in adj[cur]:
            if w != prev and w != s and w not in used:
                used.add(w)
                if dfs(w, cur, d+1, s, used):
                    return True
                used.discard(w)
        return False
    for s in range(n):
        for a in adj[s]:
            if a <= s:
                continue
            if dfs(a, s, 0, s, {s, a}):
                return True
    return False
def has16(adj, n):
    nbr = [set(a) for a in adj]
    def dfs(cur, prev, d, s, used):
        if d == 14:
            return s in nbr[cur]
        for w in adj[cur]:
            if w != prev and w != s and w not in used:
                used.add(w)
                if dfs(w, cur, d+1, s, used):
                    return True
                used.discard(w)
        return False
    for s in range(n):
        for a in adj[s]:
            if a <= s:
                continue
            if dfs(a, s, 0, s, {s, a}):
                return True
    return False

nfile = sys.argv[1]
k = int(sys.argv[2])
lines = open(nfile).read().splitlines()
# collect (line_idx, label) for 4-free graphs from C output
targets = []
for line in open(f"p2check_{nfile.split('_')[-1].replace('.g6','')}.out"):
    if line.startswith("G") and line[1:].split(" ")[0].isdigit():
        p = line.split()
        gi = int(p[0][1:])
        if "8C" in p[2]:
            targets.append((gi-1, "8C"))
        elif "16C" in p[2]:
            targets.append((gi-1, "16C"))
        elif "FREE" in p[2]:
            targets.append((gi-1, "FREE"))
print(f"n={nfile}: 4-free graphs per C = {len(targets)}")
random.seed(12345)
sample = random.sample(targets, min(k, len(targets)))
bad = 0
for gi, label in sample:
    n, adj = decode(lines[gi])
    if label == "8C":
        ok = has8(adj, n)
    else:  # 16C or FREE
        ok = (not has8(adj, n)) and has16(adj, n) if label == "16C" else (not has8(adj, n) and not has16(adj, n))
    if not ok:
        bad += 1
        print(f"  MISMATCH G{gi+1} label={label}")
print(f"  checked {len(sample)}, mismatches: {bad}")
