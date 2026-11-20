"""
Spelling-variant extractor (unit-cost Levenshtein, no context step).
Pipeline: tokenize -> count -> candidate pairs (char n-gram index)
          -> Levenshtein DP w/ backtrace -> rule filters -> CSV

Usage: python spelling_variants_nocost.py corpus.txt Variants.csv
"""
import csv
import re
import sys
from collections import Counter, defaultdict

# ---------------- tunable parameters ----------------
MIN_LEN = 5              # short words (opo/upo) are too ambiguous
MIN_COUNT = 10            # ignore hapax / typos
MIN_RATIO = 0.01         # rarer/commoner count; filters typos next to a huge word
MAX_OPS = 2              # max edit operations (= edit distance cap)
MAX_INDELS = 1           # max insertions/deletions among those ops
NGRAM_N = 3              # char n-gram size for candidate generation
NGRAM_DICE = 0.45        # min Dice overlap to even run the DP

# Plausible orthographic alternations (edit to your language).
PLAUSIBLE = [
    {"o", "u"}, {"e", "i"}, {"c", "k"}, {"c", "s"}, {"d", "r"},
    {"f", "p"}, {"b", "v"}, {"j", "h"}, {"w", "u"}, {"y", "i"},
]


def tokenize(line):
    line = re.sub(r"<[^>]*>", " ", line)
    return re.findall(r"[^\W\d_]+", line.lower())


def doubled(s, k):
    """True if s[k] is part of a doubled letter (e.g. the 2nd n in 'isanng')."""
    return (k > 0 and s[k] == s[k - 1]) or (k + 1 < len(s) and s[k] == s[k + 1])


def edit_ops(a, b):
    """Standard Levenshtein DP (all edits cost 1) with backtrace.
    Returns (distance, ops); ops = list of (kind, char_in_a, char_in_b, is_doubled)."""
    n, m = len(a), len(b)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = i
    for j in range(1, m + 1):
        D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(
                D[i - 1][j - 1] + (a[i - 1] != b[j - 1]),
                D[i - 1][j] + 1,
                D[i][j - 1] + 1,
            )
    ops, i, j = [], n, m                      # backtrace
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i][j] == D[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            if a[i - 1] != b[j - 1]:
                ops.append(("sub", a[i - 1], b[j - 1], False))
            i, j = i - 1, j - 1
        elif i > 0 and D[i][j] == D[i - 1][j] + 1:
            ops.append(("del", a[i - 1], "", doubled(a, i - 1)))
            i -= 1
        else:
            ops.append(("ins", "", b[j - 1], doubled(b, j - 1)))
            j -= 1
    ops.reverse()
    return D[n][m], ops


def ngrams(w, n=NGRAM_N):
    p = f"^{w}$"
    return {p[i:i + n] for i in range(len(p) - n + 1)}


def candidate_pairs(vocab):
    """Inverted index on char n-grams; yields pairs with high Dice overlap."""
    grams = {w: ngrams(w) for w in vocab}
    index = defaultdict(list)
    for w, gs in grams.items():
        for g in gs:
            index[g].append(w)
    for w, gs in grams.items():
        shared = Counter()
        for g in gs:
            for v in index[g]:
                if v > w:
                    shared[v] += 1
        for v, c in shared.items():
            if abs(len(v) - len(w)) > MAX_OPS:
                continue
            if 2 * c / (len(gs) + len(grams[v])) >= NGRAM_DICE:
                yield w, v


def describe(ops):
    return ", ".join(f"{x or '-'} vs. {y or '-'}" for _, x, y, _ in ops)


def flip(ops):
    swap = {"ins": "del", "del": "ins"}
    return [(swap.get(k, k), y, x, d) for k, x, y, d in ops]


def is_variant(a, b, counts):
    dist, ops = edit_ops(a, b)
    if not ops or dist > MAX_OPS:
        return None
    if sum(k != "sub" for k, _, _, _ in ops) > MAX_INDELS:
        return None                               # too many insertions/deletions
    if any(k == "sub" and {x, y} not in PLAUSIBLE for k, x, y, _ in ops):
        return None                               # arbitrary swap -> likely a different word
    if any(k != "sub" and not d for k, _, _, d in ops):
        return None                               # indel not on a doubled letter (misang, bisang...)
    if min(counts[a], counts[b]) / max(counts[a], counts[b]) < MIN_RATIO:
        return None                               # rare word next to a huge one -> typo/other word
    return ops


def main(src, out):
    with open(src, encoding="utf-8", errors="ignore") as f:
        counts = Counter(t for line in f for t in tokenize(line))
    vocab = [w for w, c in counts.items() if len(w) >= MIN_LEN and c >= MIN_COUNT]

    rows = []
    for a, b in candidate_pairs(vocab):
        ops = is_variant(a, b, counts)
        if ops is None:
            continue
        w1, w2 = (a, b) if counts[a] <= counts[b] else (b, a)
        if (w1, w2) != (a, b):
            ops = flip(ops)
        rows.append([w1, w2, counts[w1], counts[w2], describe(ops)])

    rows.sort(key=lambda r: -(r[2] + r[3]))
    with open(out, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["word1", "word2", "word1_count", "word2_count", "character_difference"])
        wr.writerows(rows)
    print(f"{len(rows)} pairs written to {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])