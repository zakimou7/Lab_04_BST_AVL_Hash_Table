"""Lab 4 - BST, AVL and hash-table performance (reference solution)."""
import random, math, sys
sys.setrecursionlimit(20000)


# ------------------------------------------------------------------ plain BST
class BST:
    def __init__(self):
        self.root = None            # node = [key, left, right]

    def insert(self, k):
        if self.root is None:
            self.root = [k, None, None]
            return
        cur = self.root
        while True:
            i = 1 if k < cur[0] else 2
            if cur[i] is None:
                cur[i] = [k, None, None]
                return
            cur = cur[i]

    def search(self, k):
        """returns (found, visited_nodes)"""
        cur, visited = self.root, 0
        while cur is not None:
            visited += 1
            if k == cur[0]:
                return True, visited
            cur = cur[1] if k < cur[0] else cur[2]
        return False, visited

    def height(self):               # in nodes (empty tree = 0)
        h, level = 0, [self.root] if self.root else []
        while level:
            h += 1
            level = [c for n in level for c in (n[1], n[2]) if c is not None]
        return h


# ------------------------------------------------------------------ AVL tree
class AVL:
    class N:
        __slots__ = ("k", "l", "r", "h")
        def __init__(self, k):
            self.k, self.l, self.r, self.h = k, None, None, 1

    def __init__(self):
        self.root = None
        self.rotations = 0

    @staticmethod
    def _h(n): return n.h if n else 0

    def _upd(self, n): n.h = 1 + max(self._h(n.l), self._h(n.r))

    def _rot_r(self, y):
        x = y.l; y.l = x.r; x.r = y
        self._upd(y); self._upd(x); self.rotations += 1
        return x

    def _rot_l(self, x):
        y = x.r; x.r = y.l; y.l = x
        self._upd(x); self._upd(y); self.rotations += 1
        return y

    def _ins(self, n, k):
        if n is None:
            return AVL.N(k)
        if k < n.k: n.l = self._ins(n.l, k)
        else:       n.r = self._ins(n.r, k)
        self._upd(n)
        bf = self._h(n.l) - self._h(n.r)
        if bf > 1:                                  # left heavy
            if self._h(n.l.l) < self._h(n.l.r):
                n.l = self._rot_l(n.l)              # left-right case
            return self._rot_r(n)
        if bf < -1:                                 # right heavy
            if self._h(n.r.r) < self._h(n.r.l):
                n.r = self._rot_r(n.r)              # right-left case
            return self._rot_l(n)
        return n

    def insert(self, k): self.root = self._ins(self.root, k)

    def search(self, k):
        cur, visited = self.root, 0
        while cur:
            visited += 1
            if k == cur.k:
                return True, visited
            cur = cur.l if k < cur.k else cur.r
        return False, visited

    def height(self): return self._h(self.root)


# ------------------------------------------------------------------ hash tables
P = (1 << 61) - 1


class HashLinear:
    """Open addressing, linear probing, FIXED size (no resizing)."""
    def __init__(self, m, seed=3):
        rnd = random.Random(seed)
        self.m, self.a, self.b = m, rnd.randrange(1, P), rnd.randrange(P)
        self.T = [None] * m

    def h(self, k): return ((self.a * k + self.b) % P) % self.m

    def insert(self, k):
        i = self.h(k)
        while self.T[i] is not None:
            i = (i + 1) % self.m
        self.T[i] = k

    def search(self, k):
        """returns (found, probes) - probes = table cells inspected"""
        i, probes = self.h(k), 0
        while True:
            probes += 1
            if self.T[i] is None:
                return False, probes
            if self.T[i] == k:
                return True, probes
            i = (i + 1) % self.m


class HashChain:
    """Separate chaining; probes = keys compared inside the chain (min 1 for an empty chain)."""
    def __init__(self, m, seed=3):
        rnd = random.Random(seed)
        self.m, self.a, self.b = m, rnd.randrange(1, P), rnd.randrange(P)
        self.T = [[] for _ in range(m)]

    def h(self, k): return ((self.a * k + self.b) % P) % self.m

    def insert(self, k): self.T[self.h(k)].append(k)

    def search(self, k):
        chain = self.T[self.h(k)]
        for pos, x in enumerate(chain, 1):
            if x == k:
                return True, pos
        return False, max(1, len(chain))


# ------------------------------------------------------------------ experiments
def tree_experiment(n=1024, seed=11):
    rnd = random.Random(seed)
    keys_sorted = list(range(1, n + 1))
    keys_random = keys_sorted[:]; rnd.shuffle(keys_random)
    out = {}
    for name, keys in (("sorted", keys_sorted), ("random", keys_random)):
        b, a = BST(), AVL()
        for k in keys:
            b.insert(k); a.insert(k)
        qs = [rnd.choice(keys) for _ in range(1000)]                         # present
        qs += [rnd.randrange(n + 1, 2 * n) for _ in range(1000)]            # absent
        def avg(T, present):
            sel = qs[:1000] if present else qs[1000:]
            return sum(T.search(q)[1] for q in sel) / len(sel)
        out[name] = dict(bst_h=b.height(), avl_h=a.height(), rot=a.rotations,
                         bst_hit=avg(b, True), bst_miss=avg(b, False),
                         avl_hit=avg(a, True), avl_miss=avg(a, False))
    return out


def hash_experiment(m=2003, loads=(0.25, 0.5, 0.75, 0.9), trials=3):
    res = []
    for alpha in loads:
        n = int(alpha * m)
        acc = dict(lin_hit=0, lin_miss=0, ch_hit=0, ch_miss=0)
        for t in range(trials):
            rnd = random.Random(100 + t)
            keys = rnd.sample(range(1, 10**9), n)
            absent = rnd.sample(range(10**9 + 1, 2 * 10**9), n)
            L, C = HashLinear(m, seed=t), HashChain(m, seed=t)
            for k in keys:
                L.insert(k); C.insert(k)
            acc["lin_hit"] += sum(L.search(k)[1] for k in keys) / n
            acc["lin_miss"] += sum(L.search(k)[1] for k in absent) / n
            acc["ch_hit"] += sum(C.search(k)[1] for k in keys) / n
            acc["ch_miss"] += sum(C.search(k)[1] for k in absent) / n
        row = {k: v / trials for k, v in acc.items()}
        row["alpha"] = alpha
        row["th_lin_hit"] = 0.5 * (1 + 1 / (1 - alpha))
        row["th_lin_miss"] = 0.5 * (1 + 1 / (1 - alpha) ** 2)
        row["th_ch_hit"] = 1 + alpha / 2
        row["th_ch_miss"] = alpha + math.exp(-alpha)   # E[max(1, chain length)]
        res.append(row)
    return res


def report():
    from display import banner, section, note, table, ci, figure, save, show_all
    banner("LAB 4 — BST, AVL et Hash tables")
    section("1. Arbres : hauteur et coût de recherche (n = 1024)")
    T = tree_experiment(1024)
    rows = []
    for name, lab in (("sorted", "insertion triée"), ("random", "insertion aléatoire")):
        r = T[name]
        rows.append([lab, r["bst_h"], r["avl_h"], r["rot"], f"{r['bst_hit']:.1f}", f"{r['bst_miss']:.1f}", f"{r['avl_hit']:.1f}", f"{r['avl_miss']:.1f}"])
    table(["Données", "hauteur BST", "hauteur AVL", "rotations AVL", "BST hit", "BST miss", "AVL hit", "AVL miss"], rows)
    note("Insertion triée: BST = liste chaînée (hauteur n) ⇒ search Θ(n). AVL yb9a hauteur ≈ log2 n (≤ 1.44·log2(n+2)) b ta7t rotations.")
    section("2. Hash tables (m = 2003) : probes moyens selon le load factor α")
    H = hash_experiment()
    table(["α", "probing hit", "théorie", "probing miss", "théorie", "chaining hit", "théorie", "chaining miss", "théorie"],
          [[f"{h['alpha']:.2f}", f"{h['lin_hit']:.2f}", f"{h['th_lin_hit']:.2f}", f"{h['lin_miss']:.2f}", f"{h['th_lin_miss']:.2f}",
            f"{h['ch_hit']:.2f}", f"{h['th_ch_hit']:.2f}", f"{h['ch_miss']:.2f}", f"{h['th_ch_miss']:.2f}"] for h in H])
    note("Linear probing yekherreb bezzaf ki α → 1 (miss ≈ 1/(1-α)²); chaining yzid b rfq (linéaire f α).")
    fig, ax = figure(1, 3, figsize=(14, 4))
    if fig:
        labels = ["insertion triée", "insertion aléatoire"]; x = range(2); w = 0.35
        ax[0].bar([i - w / 2 for i in x], [T["sorted"]["bst_h"], T["random"]["bst_h"]], w, label="BST")
        ax[0].bar([i + w / 2 for i in x], [T["sorted"]["avl_h"], T["random"]["avl_h"]], w, label="AVL")
        ax[0].set_xticks(list(x)); ax[0].set_xticklabels(labels); ax[0].set_yscale("log"); ax[0].set_ylabel("hauteur (n = 1024)"); ax[0].set_title("Hauteur BST vs AVL"); ax[0].legend()
        al = [h["alpha"] for h in H]
        for a, (k1, k2, t) in zip(ax[1:], (("lin_hit", "ch_hit", "Search réussie (hit)"), ("lin_miss", "ch_miss", "Search échouée (miss)"))):
            a.plot(al, [h[k1] for h in H], "o-", label="linear probing"); a.plot(al, [h[k2] for h in H], "s-", label="chaining")
            a.plot(al, [h["th_" + k1] for h in H], "k:", label="théorie probing")
            a.set_xlabel("load factor α"); a.set_ylabel("probes moyens"); a.set_title(t); a.legend()
            if "miss" in k1: a.set_yscale("log")
        save(fig, "lab04_structures")
    show_all()


if __name__ == "__main__":
    report()
