#!/usr/bin/env python3
"""g6conv — decode this nauty build's graph6 output (BIAS6=63) into
'G n e' + adjacency lines (for p2check). Usage: g6conv < in.g6 > out.lst
Only handles cubic/simple graphs as emitted by: geng n 3n/2:3n/2 -d3 -D3 -c -q
"""
import sys

BIAS6 = 63

def decode(line):
    n = ord(line[0]) - BIAS6
    if not (2 <= n <= 63):
        return None
    total = n * (n - 1) // 2
    if len(line) - 1 < (total + 5) // 6:
        return None
    # bit stream: for j in 1..n-1, i in 0..j-1
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

def main():
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line or line[0] in "!#":
            continue
        d = decode(line)
        if d is None:
            continue
        n, adj = d
        if any(len(a) != 3 for a in adj):
            continue  # not cubic: skip (safety)
        e = n * 3 // 2
        print(f"G {n} {e}")
        for v in range(n):
            print(f"{v+1}: {adj[v][0]+1} {adj[v][1]+1} {adj[v][2]+1}")

if __name__ == "__main__":
    main()
