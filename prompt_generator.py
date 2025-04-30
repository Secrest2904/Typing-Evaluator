#!/usr/bin/env python3
"""
prompt_generator.py

Generates a typing prompt by sampling a snippet aligned to full sentences
(190–210 characters), always starting at a sentence boundary and ending
exactly at a sentence boundary. “Hard” prompts must contain quotation marks.

Usage:
  • Import get_random_prompt(difficulty) in your backend.
  • Or run standalone: python prompt_generator.py --difficulty hard
"""

import os
import re
import random
import argparse

# ─── Configuration ─────────────────────────────────────────────────────────
MIN_LEN = 190
MAX_LEN = 210

# Locate the source text
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TXT_PATH = os.path.join(BASE_DIR, "files", "moby_dick.txt")

# ─── Load & Clean Body Text ─────────────────────────────────────────────────

def load_body_text(path=TXT_PATH):
    """Read and clean the text, stripping Gutenberg headers if present."""
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    # Strip Gutenberg header
    start = raw.find("*** START OF THIS PROJECT GUTENBERG EBOOK")
    if start != -1:
        raw = raw[raw.find("\n", start) + 1:]
    # Strip Gutenberg footer
    end = raw.find("*** END OF THIS PROJECT GUTENBERG EBOOK")
    if end != -1:
        raw = raw[:end]
    # Collapse whitespace
    text = raw.replace("\r\n", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()

BODY_TEXT = load_body_text()

# ─── Sentence Boundary Indices ───────────────────────────────────────────────
# start positions: immediately after . ! or ? plus whitespace
sentence_starts = [0] + [m.end() for m in re.finditer(r'(?<=[\.\!?])\s+', BODY_TEXT)]
# end positions: index of punctuation before whitespace
sentence_ends   = [m.start() for m in re.finditer(r'(?<=[\.\!?])\s+', BODY_TEXT)]

# ─── Prompt Generation ─────────────────────────────────────────────────────

def get_random_prompt(difficulty: str) -> str:
    """
    Return a random snippet of the given difficulty ('easy' or 'hard').
    Starts and ends at sentence boundaries; 'hard' requires at least one quote.
    """
    difficulty = difficulty.lower()
    for _ in range(1000):
        start = random.choice(sentence_starts)
        # valid ends give snippet lengths within bounds
        valid_ends = [e for e in sentence_ends if MIN_LEN <= (e - start) <= MAX_LEN]
        if not valid_ends:
            continue
        end = random.choice(valid_ends)
        snippet = BODY_TEXT[start:end]
        # skip artifacts
        if '[[' in snippet or ']]' in snippet:
            continue
        # require quotes for hard, and absence for easy
        has_quote = '"' in snippet or '“' in snippet or '”' in snippet
        if difficulty == 'hard' and not has_quote:
            continue
        if difficulty == 'easy' and has_quote:
            continue
        return snippet
    # fallback: first full sentence(s) up to MIN_LEN
    for e in sentence_ends:
        if e >= MIN_LEN:
            return BODY_TEXT[:e]
    return BODY_TEXT[:MIN_LEN]

# ─── CLI Support ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a typing prompt.')
    parser.add_argument('--difficulty', choices=['easy','hard'], default='easy',
                        help='Choose prompt difficulty')
    args = parser.parse_args()
    print(get_random_prompt(args.difficulty))
