# Filipino Spelling Variant Finder

A Python pipeline that processes a Tagalog Wikipedia dump, filters it down to a clean Filipino vocabulary, and (in later stages) finds spelling variants of Filipino words using edit distance and n-gram blocking.

## Requirements

- **Python 3.9+**
- **pip** (bundled with Python)

### Dependencies

| Package | Version | Purpose |
|---|---|---|
| `wordfreq` | `>=3.1` | Tagalog word-frequency lookup (`zipf_frequency`), used to filter non-Filipino tokens |
