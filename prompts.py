# seed_prompts_fixed_length.py

import os
import re
import requests
from pymongo import MongoClient

# ─── CONFIG ────────────────────────────────────────────────────────────────
MONGO_URI   = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME     = "typing_test"
COL_NAME    = "prompts"
TARGET_LEN  = 80    # all prompts will be exactly 80 chars long
SYMBOL_THRESH = 5   # easy = ≤5 non-letter chars; hard = >5

# ─── SETUP ────────────────────────────────────────────────────────────────
client      = MongoClient(MONGO_URI)
db          = client[DB_NAME]
prompts_col = db[COL_NAME]

# ─── FETCH SOURCE ─────────────────────────────────────────────────────────
resp = requests.get("https://type.fit/api/quotes")
resp.raise_for_status()
all_quotes = resp.json()   # list of { "text": "...", "author": "..." }

# ─── UTILITY ──────────────────────────────────────────────────────────────
def extract_snippet(s: str, length: int) -> str:
    """
    Normalize whitespace, then truncate/pad to exactly `length` chars.
    """
    # collapse whitespace
    s = re.sub(r"\s+", " ", s.strip())
    if len(s) >= length:
        return s[:length]
    # optionally pad with spaces if you want exactly length:
    return s.ljust(length)

def count_non_letters(s: str) -> int:
    return sum(1 for c in set(s) if not (c.isalpha() or c.isspace()))

# ─── BUILD DOCUMENTS ──────────────────────────────────────────────────────
easy_docs = []
hard_docs = []

for q in all_quotes:
    text = q.get("text", "").strip()
    if len(text) < TARGET_LEN:
        continue            # skip too-short quotes

    snippet = extract_snippet(text, TARGET_LEN)
    sym_count = count_non_letters(snippet)

    if sym_count <= SYMBOL_THRESH:
        easy_docs.append({"difficulty": "easy", "text": snippet})
    else:
        hard_docs.append({"difficulty": "hard", "text": snippet})

print(f"Found {len(easy_docs)} easy snippets, {len(hard_docs)} hard snippets.")

# ─── SEED DATABASE ─────────────────────────────────────────────────────────
prompts_col.delete_many({})            # WARNING: clears existing prompts
if easy_docs:
    prompts_col.insert_many(easy_docs)
if hard_docs:
    prompts_col.insert_many(hard_docs)

print("Seeding complete.")
