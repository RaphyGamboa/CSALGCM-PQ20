# config.py

# Paths/Directories
DATASET_PATH = "../data/Raw.txt"
CLEANED_PATH = "../data/Cleaned.txt"
VOCAB_CACHE = "../cache/vocab.pkl"
OUTPUT_CSV = "../output/variants.csv"

# Input 
ENCODING = "utf-8"
ERRORS = "ignore"

# Thresholds
MIN_TOKEN_LEN = 5
MIN_FREQ = 10

# Constants

# CSV Header
CSV_HEADER = ["word_1", "word_2", "word1_count", "word2_count", "character_difference"]