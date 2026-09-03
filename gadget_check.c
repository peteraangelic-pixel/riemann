/* gadget_check — search for Bensmail edge-gadget cores K for Erdős–Gyárfás #64.
 *
 * Input: graph6 (BIAS6=63, as emitted by this nauty build), one graph per line.
 *
 * A core K is a connected cubic graph on n vertices (n even) such that:
 *   (a) all simple cycles of K have length NOT in {4, 8, 16, 32};
 *   (b) for some pair (a, b): every simple a-b path has length NOT in {2, 6, 14, 30}.
 * (For n <= 62 these are the only relevant powers/offsets.)
 *
 * If found: prints the g6 line, n, the pair, the full cycle-length set of K,
 * and the full simple a-b path length multiset-free SET for that pair.
 *
 * Path searches use DFS with early exit; the L=30 search has a node budget per
 * pair (BUDGET30) to keep the sweep fast — unverified pairs are flagged so the
 * final candidate can be re-verified exactly.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAXN 80
#define BUDGET30 40000000LL   /* node-expansion budget for the L=30 search per pair */

static int n;
static int adj[MAXN][3];
static int degv[MAXN];

/* ---------- graph6 decode (BIAS6=63, nauty column order) ---------- */
static int decode_g6(const char *line, int out_adj[][3]) {
    int n0 = (unsigned char)line[0] - 63;
    if (n0 < 4 || n0 > MAXN) return 0;
    int total = n0 * (n0 - 1) / 2;
    int need = (total + 5) / 6;
    if ((int)strlen(line) < 1 + need) return 0;
    int bits[6000];
    int bn = 0;
    for (int p = 1; p < 1 + need; p++) {
        int v = (unsigned char)line[p] - 63;
        if (v < 0 || v > 63) return 0;
        for (int b = 5; b >= 0; b--) bits[bn++] = (v >> b) & 1;
    }
    for (int i = 0; i < n0; i++) degv[i] = 0;
    int idx = 0;
    for (int j = 1; j < n0; j++) {
        for (int i = 0; i < j; i++) {
            if (bits[idx++]) {
                if (degv[i] >= 3 || degv[j] >= 3) { degv[i] = degv[j] = 99; }
                else {
                    out_adj[i][degv[i]++] = j;
                    out_adj[j][degv[j]++] = i;
                }
            }
        }
    }
    for (int i = 0; i < n0; i++) if (degv[i] != 3) return 0;
    return n0;
}

/* ---------- cycle enumeration (canonical: start at min vertex) ---------- */
static int CYCLE_BAD(int L) { return (L == 4 || L == 8 || L == 16 || L == 32); }
static int cyclens_seen[80];   /* set of cycle lengths seen */
static int cycle_set_count;
static long long cycle_total;

static int has_adj(int u, int v) {
    for (int k = 0; k < 3; k++) if (adj[u][k] == v) return 1;
    return 0;
}

/* DFS for simple cycles: start vertex s, only visit vertices > s,
 * depth = edges used. Returns 1 if a bad cycle length found (early exit). */
static int vis_c[MAXN];
static int cycle_dfs(int cur, int s, int depth) {
    if (CYCLE_BAD(depth + 1) && has_adj(cur, s)) {
        int L = depth + 1;
        for (int k = 0; k < cycle_set_count; k++) if (cyclens_seen[k] == L) return 1;
        if (cycle_set_count < 80) cyclens_seen[cycle_set_count++] = L;
        return 1;
    }
    if (depth + 1 > 32) return 0;
    for (int k = 0; k < 3; k++) {
        int w = adj[cur][k];
        if (w > s && !vis_c[w]) {
            if (w == s) continue;
            vis_c[w] = 1;
            cycle_total++;
            if (cycle_dfs(w, s, depth + 1)) { vis_c[w] = 0; return 1; }
            vis_c[w] = 0;
        }
    }
    return 0;
}

/* ---------- exact-length simple path search between a and b ---------- */
static int vis_p[MAXN];
static long long budget_left;

/* returns 1 if a simple path of exactly L edges from a to b exists */
static int path_dfs(int cur, int a, int b, int depth, int L) {
    if (budget_left <= 0) return 0;
    budget_left--;
    if (depth == L) return (cur == b);
    for (int k = 0; k < 3; k++) {
        int w = adj[cur][k];
        if (!vis_p[w] && w != a) {
            vis_p[w] = 1;
            if (path_dfs(w, a, b, depth + 1, L)) { vis_p[w] = 0; return 1; }
            vis_p[w] = 0;
        }
    }
    return 0;
}

static int common_neighbor(int a, int b) {
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            if (adj[a][i] == adj[b][j]) return 1;
    return 0;
}

/* record every simple a-b path length into set (for the final report) */
static int pathlen_set[80];
static int pathlen_count;
static long long allpaths_budget;

static void collect_path_dfs(int cur, int a, int b, int depth) {
    if (allpaths_budget <= 0) return;
    allpaths_budget--;
    if (cur == b) {
        for (int k = 0; k < pathlen_count; k++) if (pathlen_set[k] == depth) return;
        if (pathlen_count < 80) pathlen_set[pathlen_count++] = depth;
        return;
    }
    if (depth >= n) return;
    for (int k = 0; k < 3; k++) {
        int w = adj[cur][k];
        if (!vis_p[w] && w != a) {
            vis_p[w] = 1;
            collect_path_dfs(w, a, b, depth + 1);
            vis_p[w] = 0;
        }
    }
}

static long long graphs_seen;
static long long graphs_girth5;

int main(void) {
    char line[2048];
    int local_adj[MAXN][3];
    long long found = 0;
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\n")] = 0;
        if (!line[0] || line[0] == '!') continue;
        n = decode_g6(line, local_adj);
        if (!n) continue;
        memcpy(adj, local_adj, sizeof local_adj);
        graphs_seen++;

        /* (a) cycles */
        for (int i = 0; i < 80; i++) vis_c[i] = 0;
        for (int i = 0; i < 80; i++) vis_p[i] = 0;
        for (int i = 0; i < 80; i++) cyclens_seen[i] = 0;
        cycle_set_count = 0; cycle_total = 0;
        int bad = 0;
        for (int s = 0; s < n && !bad; s++) {
            vis_c[s] = 1;
            bad = cycle_dfs(s, s, 0);
            vis_c[s] = 0;
        }
        if (bad) continue;
        graphs_girth5++;
        int girth5 = 1;
        for (int k = 0; k < cycle_set_count; k++) if (cyclens_seen[k] == 3 || cyclens_seen[k] == 4) girth5 = 0;

        /* (b) find a good pair */
        for (int a = 0; a < n && !found; a++) {
            for (int b = a + 1; b < n; b++) {
                if (common_neighbor(a, b)) continue;              /* L=2 */
                int fail = 0;
                for (int L = 6; L <= 14 && !fail; L += 8) {
                    for (int i = 0; i < MAXN; i++) vis_p[i] = 0;
                    vis_p[a] = 1;
                    budget_left = 20000000LL;
                    if (path_dfs(a, a, b, 0, L)) fail = 1;
                }
                if (fail) continue;
                int fail30 = 0, unverified30 = 0;
                if (n - 1 >= 30) {
                    for (int i = 0; i < MAXN; i++) vis_p[i] = 0;
                    vis_p[a] = 1;
                    budget_left = BUDGET30;
                    if (path_dfs(a, a, b, 0, 30)) fail30 = 1;
                    else if (budget_left <= 0) unverified30 = 1;
                }
                if (fail30) continue;
                found++;
                for (int i = 0; i < MAXN; i++) vis_p[i] = 0;
                pathlen_count = 0;
                allpaths_budget = 200000000LL;
                vis_p[a] = 1;
                collect_path_dfs(a, a, b, 0);
                char cycs[1024] = "", pls[1024] = "";
                for (int k = 0; k < cycle_set_count; k++)
                    snprintf(cycs + strlen(cycs), 1024 - strlen(cycs), " %d", cyclens_seen[k]);
                for (int k = 0; k < pathlen_count; k++)
                    snprintf(pls + strlen(pls), 1024 - strlen(pls), " %d", pathlen_set[k]);
                printf("GADGET n=%d pair=(%d,%d)%s girth5=%d\n  g6: %s\n  cycles:%s\n  a-b path lens:%s\n",
                       n, a, b, unverified30 ? " [30-path UNVERIFIED]" : "", girth5, line, cycs, pls);
                fflush(stdout);
            }
        }
    }
    fprintf(stderr, "graphs=%lld with_girth5=%lld gadgets_found=%lld\n",
            graphs_seen, graphs_girth5, found);
    return 0;
}
