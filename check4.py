#!/usr/bin/env python3
"""Verify C's 4-cycle-free labels via the trace formula c4=(tr(A^4)-2*sum(d^2)+2m)/8."""
import random, sys
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
def mm(B, C, n):
    return [[sum(B[i][k]*C[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
def c4(A, n, m):
    A2 = mm(A, A, n)
    A4 = mm(A2, A2, n)
    tr = sum(A4[i][i] for i in range(n))
    sd2 = sum(A2[i][j] for i in range(n) for j in range(n))
    return (tr - 2*sd2 + 2*m)//8
nfile = sys.argv[1]
k = int(sys.argv[2])
lines = open(nfile).read().splitlines()
name = nfile.split('_')[-1].replace('.g6','')
labels = {}
for line in open(f"p2check_{name}.out"):
    if line.startswith("G") and line[1:].split(" ")[0].isdigit():
        p = line.split()
        gi = int(p[0][1:])
        labels[gi] = p[2]
random.seed(777)
free4 = [gi for gi, lab in labels.items() if not lab.startswith("4C")]
with4 = [gi for gi, lab in labels.items() if lab.startswith("4C")]
sample_free = random.sample(free4, min(k, len(free4)))
sample_w = random.sample(with4, min(k//2, len(with4)))
bad = 0
for gi in sample_free:
    n, adj = decode(lines[gi-1])
    A = [[0]*n for _ in range(n)]
    for u in range(n):
        for v in adj[u]: A[u][v] = 1
    c = c4(A, n, 3*n//2)
    if c != 0:
        bad += 1; print(f"  MISMATCH free-label G{gi}: c4={c}")
for gi in sample_w:
    n, adj = decode(lines[gi-1])
    A = [[0]*n for _ in range(n)]
    for u in range(n):
        for v in adj[u]: A[u][v] = 1
    c = c4(A, n, 3*n//2)
    clab = int(labels[gi][3:-1])
    if c <= 0 or c != clab:
        bad += 1; print(f"  MISMATCH with4-label G{gi}: py={c} lab={clab}")
print(f"n={name}: free4-sample {len(sample_free)}/{len(free4)}, with4-sample {len(sample_w)}/{len(with4)}, mismatches: {bad}")
