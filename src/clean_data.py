# clean_data.py - the whole contract
# Raw.txt -> Cleaned.txt
#
# Line-level cleanup only:
#  - strip [http://...] links and bare URLs
#  - drop lines that are mostly non-Latin script
#  - strip leftover bullet markers
#  - collapse whitespace
#
# Does NOT tokenize. Does NOT filter words. Does NOT call wordfreq.
# Output is a text file you can read, grep, and eyeball.

import re
import sys
from pathlib import Path

import config


_URL_RE    = re.compile(r"\[https?://[^\]]*\]|https?://\S+")
_BULLET_RE = re.compile(r"^[•·\u2022\-\*]+\s*")


def is_latin_heavy(line: str, threshold: float = 0.75) -> bool:
    if not line:
        return False
    latin = sum(1 for c in line if c.isascii() or c in "ñÑáéíóúÁÉÍÓÚ’")
    return latin / len(line) >= threshold


def clean_line(line: str) -> str | None:
    # Return cleaned line, or None if the line should be dropped.
    line = _URL_RE.sub(" ", line)
    if not is_latin_heavy(line):
        return None
    line = _BULLET_RE.sub("", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line or None


def clean_file(src: str, dst: str) -> tuple[int, int]:
    # Read src, write dst. Returns (lines_in, lines_out).
    n_in = n_out = 0
    with open(src, encoding=config.ENCODING, errors=config.ERRORS) as fin, \
         open(dst, "w", encoding=config.ENCODING) as fout:
        for line in fin:
            n_in += 1
            cleaned = clean_line(line)
            if cleaned is not None:
                fout.write(cleaned)
                fout.write("\n")
                n_out += 1
    return n_in, n_out


def main() -> None:
    src = Path(config.DATASET_PATH)
    dst = Path(config.CLEANED_PATH)
    if not src.exists():
        sys.exit(f"corpus not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    print(f"reading {src}  ({src.stat().st_size / 1e6:.1f} MB)")
    n_in, n_out = clean_file(str(src), str(dst))
    print(f"  lines in:  {n_in:>10,}")
    print(f"  lines out: {n_out:>10,}  ({100 * n_out / n_in:.1f}%)")
    print(f"  wrote {dst}")


if __name__ == "__main__":
    main()