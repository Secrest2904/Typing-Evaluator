#!/usr/bin/env python3
"""
seed_prompts.py

Seeds the MongoDB 'typing_test.prompts' collection with variable-length text snippets
(190–210 characters), always starting and ending at sentence boundaries.

Usage:
  1. Ensure `pride_prejudice.txt` is in the same folder.
  2. Activate your env (e.g. conda activate typingtest).
  3. Run: python seed_prompts.py
"""

import os
import re
import random
from pymongo import MongoClient

# ─── Configuration ─────────────────────────────────────────────────────────
MONGO_URI     = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME       = "typing_test"
COL_NAME      = "prompts"
MIN_LEN       = 190       # minimum characters per prompt
MAX_LEN       = 210       # maximum characters per prompt
SYMBOL_THRESH = 6        # non-letter threshold for difficulty
N_SAMPLES     = 500       # how many prompts to generate

# ─── MongoDB Setup ──────────────────────────────────────────────────────────
client      = MongoClient(MONGO_URI)
db          = client[DB_NAME]
prompts_col = db[COL_NAME]

# ─── Load & Clean Source Text ───────────────────────────────────────────────
def load_body_text(filename="pride_prejudice.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        raw = f.read()

    start_marker = "*** START OF THIS PROJECT GUTENBERG EBOOK"
    end_marker   = "*** END OF THIS PROJECT GUTENBERG EBOOK"

    s_idx = raw.find(start_marker)
    s_idx = raw.find("\n", s_idx) + 1 if s_idx != -1 else 0

    e_idx = raw.find(end_marker)
    e_idx = e_idx if e_idx != -1 else len(raw)

    body = raw[s_idx:e_idx]
    body = body.replace("\r\n", " ").replace("\n", " ")
    body = re.sub(r"\s+", " ", body).strip()
    return body

body = load_body_text()

# ─── Verify Length ──────────────────────────────────────────────────────────
if len(body) < MIN_LEN:
    raise RuntimeError(
        f"Source text length ({len(body)}) is shorter than MIN_LEN ({MIN_LEN})."
    )

# ─── Sentence Boundaries ────────────────────────────────────────────────────
# Indices where a new sentence starts (after .!? and whitespace)
sentence_starts = [0] + [m.end() for m in re.finditer(r'(?<=[\.\!?])\s+', body)]
# Indices where a sentence ends (before whitespace after punctuation)
sentence_ends   = [m.start() for m in re.finditer(r'(?<=[\.\!?])\s+', body)]

# Filter valid ranges
sentence_starts = [i for i in sentence_starts if i <= len(body) - MIN_LEN]
sentence_ends   = [e for e in sentence_ends   if e >= MIN_LEN]

if not sentence_starts or not sentence_ends:
    raise RuntimeError(
        "No valid sentence boundaries for specified MIN_LEN and text source."
    )

# ─── Utility ────────────────────────────────────────────────────────────────
def count_non_letters(s: str) -> int:
    return sum(1 for c in set(s) if not (c.isalpha() or c.isspace()))

# ─── Build Prompt Documents ─────────────────────────────────────────────────
docs = {"easy": [], "hard": []}
count = 0
attempts = 0
max_attempts = N_SAMPLES * 10

while count < N_SAMPLES and attempts < max_attempts:
    attempts += 1
    start = random.choice(sentence_starts)
    # find end indices that yield snippet length within [MIN_LEN, MAX_LEN]
    candidates = [e for e in sentence_ends if MIN_LEN <= e - start <= MAX_LEN]
    if not candidates:
        continue
    end = random.choice(candidates)
    snippet = body[start:end]
	# skip any snippets that contain "[[" or "]]"
    if '[[' in snippet or ']]' in snippet:
        continue

    sym_count = count_non_letters(snippet)
    difficulty = "easy" if sym_count <= SYMBOL_THRESH else "hard"
    docs[difficulty].append({"difficulty": difficulty, "text": snippet})
    count += 1

print(f"Prepared {len(docs['easy'])} easy and {len(docs['hard'])} hard prompts.")

# ─── Seed MongoDB ──────────────────────────────────────────────────────────
prompts_col.delete_many({})
if docs["easy"]:
    prompts_col.insert_many(docs["easy"])
if docs["hard"]:
    prompts_col.insert_many(docs["hard"])
print("Seeding complete.")
