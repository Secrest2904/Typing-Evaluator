#!/usr/bin/env python3
# backend.py

import os
import sys
import random
from prompt_generator import get_random_prompt

# Directory where files/ lives
BASE_DIR  = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
FILES_DIR = os.path.join(BASE_DIR, "files")

def load_prompts(difficulty):
    # simply returns a one-element list so frontend.load_prompt still works
    return [ get_random_prompt(difficulty) ]

def get_random_prompt_wrapper(difficulty):
    # keep naming consistent
    return get_random_prompt(difficulty)

def save_to_leaderboard(name: str, wpm: int, mistakes: int, difficulty: str) -> None:
    os.makedirs(FILES_DIR, exist_ok=True)
    lb = os.path.join(FILES_DIR, "leaderboard.txt")
    with open(lb, "a", encoding="utf-8") as f:
        f.write(f"{difficulty.capitalize()} - {name} - WPM: {wpm}, Mistakes: {mistakes}\n")
