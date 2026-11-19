# text_process.py
# Cleaned.txt -> cache/vocab.pkl
# 
# Tokenizes clean text and produces the filtered {word: count} vocabulary.
# This is where word-level filtering happens.

import pickle
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

from wordfreq import zipf_frequency

import config


# Tokenizer
TOKEN_RE = re.compile(r"[a-zñ]+(?:[-'’][a-zñ]+)*", re.IGNORECASE)
APOSTROPHE_RE = re.compile(r"['’]")
VALID_WORD_RE = re.compile(r"[a-zñ]+(?:-[a-zñ]+)*")
VOWELS = set("aeiouñ")


def iter_tokens(line: str) -> Iterator[str]:
    # Yield lowercase tokens; strip apostrophe clitics; keep hyphens.
    for match in TOKEN_RE.finditer(line):
        tok = match.group(0).lower()
        head = APOSTROPHE_RE.split(tok, maxsplit=1)[0]
        if head:
            yield head


# Filtering
def _is_tagalog(word: str) -> bool:
    if zipf_frequency(word, "tl") >= config.ZIPF_MIN:
        return True
    if "-" in word:
        return zipf_frequency(word.replace("-", ""), "tl") >= config.ZIPF_MIN
    return False


def keep(word: str) -> bool:
    if len(word) < config.MIN_TOKEN_LEN:
        return False
    if not VALID_WORD_RE.fullmatch(word):
        return False
    if not (VOWELS & set(word)):
        return False
    run = 0
    for c in word:
        if c in VOWELS or c == "-":
            run = 0
        else:
            run += 1
            if run >= config.MAX_CONSONANT_RUN + 1:
                return False
    return _is_tagalog(word)


# Build vocabulary
def build_vocab(cleaned_path: str) -> dict[str, int]:
    counter = Counter()
    with open(cleaned_path, encoding=config.ENCODING) as f:
        for line in f:
            counter.update(iter_tokens(line))
    print(f"  raw unique tokens: {len(counter):>10,}")
    vocab = {w: c for w, c in counter.items()
             if c >= config.MIN_FREQ and keep(w)}
    print(f"  kept:              {len(vocab):>10,}")
    return vocab


def main() -> None:
    src = Path(config.CLEANED_PATH)
    if not src.exists():
        raise FileNotFoundError(
            f"{src} not found - run `python clean_data.py` first"
        )
    print(f"reading {src}  ({src.stat().st_size / 1e6:.1f} MB)")
    vocab = build_vocab(str(src))
    out = Path(config.VOCAB_CACHE)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(vocab, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()