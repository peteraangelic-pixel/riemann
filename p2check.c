/* p2check — Erdos-Gyarfas problem #64: power-of-2 cycles.
 *
 * For each connected cubic (3-regular) graph given on stdin in nauty
 * "geng -L" adjacency-list format, decide whether it contains a cycle of
 * length 4, 8 or 16 (the only 2^k with k>=2 that fit in a graph with <=20
 * vertices).  A cubic graph with NONE of these is a counterexample to
 * "every graph with min degree >= 3 has a 2^k-cycle" ($1000, Erdos #64).
 *
 * Input (geng -L):  "G <n> <e>" then n lines "<v>: <nbr> <nbr> <nbr>"
 * Output: one line per graph:  G<idx> n=<n> 4C(k)/8C/16C/FREE ; FREE graphs
 * are printed afterwards in full adjacency form (vertices 1..n).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 64

static int n, e;
static int adj[MAXN][3];
static int vis[MAXN];

static int has_adj(int u, int v) {
    for (int i = 0; i < 3; i++) if (adj[u][i] == v) return 1;
    return 0;
}

/* count 4-cycles: for each edge (u,v) count pairs x~N(v)\{u}, y~N(u)\{v}
 * with x~y; each 4-cycle is counted once per its 4 edges */
static long count4(void) {
    long total = 0;
    for (int u = 0; u < n; u++)
        for (int i = 0; i < 3; i++) {
            int v = adj[u][i];
            if (v <= u) continue;
            for (int j = 0; j < 3; j++) {
                int x = adj[v][j];
                if (x == u) continue;
                for (int k = 0; k < 3; k++) {
                    int y = adj[u][k];
                    if (y == v) continue;
                    if (has_adj(x, y)) total++;
                }
            }
        }
    return total / 4;
}

/* cycle of length L+2: DFS simple paths of length L in G-{s} starting from
 * a neighbor a of s; a hit when the endpoint is a neighbor of s. */
static int dfsL(int cur, int prev, int depth, int L, int s) {
    if (depth == L) return has_adj(cur, s);
    for (int i = 0; i < 3; i++) {
        int w = adj[cur][i];
        if (w == prev || w == s || vis[w]) continue;
        vis[w] = 1;
        if (dfsL(w, cur, depth + 1, L, s)) return 1;
        vis[w] = 0;
    }
    return 0;
}

static int hasL(int L) { /* L = internal path length; cycle = L+2 */
    if (n < L + 2) return 0;
    for (int s = 0; s < n; s++)
        for (int i = 0; i < 3; i++) {
            int a = adj[s][i];
            memset(vis, 0, sizeof(vis));
            vis[s] = 1; vis[a] = 1;
            if (dfsL(a, s, 0, L, s)) return 1;
        }
    return 0;
}

int main(void) {
    static char line[256];
    int idx = 0, n4 = 0, n8 = 0, n16 = 0, nfree = 0;
    int expecting = 0;   /* vertex lines left to read for current graph */

    while (fgets(line, sizeof(line), stdin)) {
        if (line[0] == 'G') {
            int nn, ee;
            if (sscanf(line, "G %d %d", &nn, &ee) != 2) continue;
            n = nn; e = ee;
            if (n > MAXN || e != 3 * n / 2) { expecting = -1; continue; }
            for (int v = 0; v < n; v++)
                for (int i = 0; i < 3; i++) adj[v][i] = -1;
            expecting = n;
            idx++;
            continue;
        }
        if (expecting <= 0) continue;
        int v, a, b, c;
        if (sscanf(line, "%d : %d %d %d", &v, &a, &b, &c) == 4) {
            if (v < 1 || v > n || a < 1 || a > n || b < 1 || b > n || c < 1 || c > n)
                continue;
            adj[v - 1][0] = a - 1;
            adj[v - 1][1] = b - 1;
            adj[v - 1][2] = c - 1;
            if (--expecting == 0) {
                /* verify 3-regular + simple */
                int deg[MAXN] = {0}, ok = 1;
                for (int u = 0; u < n && ok; u++) {
                    for (int i = 0; i < 3; i++) {
                        int w = adj[u][i];
                        if (w == u) { ok = 0; break; }
                        for (int j = 0; j < i; j++) if (adj[u][j] == w) { ok = 0; break; }
                        deg[w]++;
                    }
                }
                for (int u = 0; u < n && ok; u++) if (deg[u] != 3) ok = 0;
                if (!ok) { printf("G%05d n=%d BAD\n", idx, n); continue; }
                long c4 = count4();
                if (c4 > 0) { n4++;  printf("G%05d n=%d 4C(%ld)\n", idx, n, c4); }
                else if (hasL(6)) { n8++;  printf("G%05d n=%d 8C\n", idx, n); }
                else if (hasL(14)) { n16++; printf("G%05d n=%d 16C\n", idx, n); }
                else {
                    nfree++;
                    printf("G%05d n=%d FREE\n", idx, n);
                    for (int u = 0; u < n; u++)
                        printf("  %d: %d %d %d\n", u + 1,
                               adj[u][0] + 1, adj[u][1] + 1, adj[u][2] + 1);
                }
            }
        }
    }
    printf("== total=%d with4=%d with8=%d with16=%d FREE=%d\n",
           idx, n4, n8, n16, nfree);
    return 0;
}
