import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EASY_PROMPT_FILE = os.path.join(BASE_DIR, "files", "Easy.txt")
HARD_PROMPT_FILE = os.path.join(BASE_DIR, "files", "Hard.txt")

LEADERBOARD_FILE = 'files/leaderboard.txt'

def load_prompts(difficulty):
    file_path = EASY_PROMPT_FILE if difficulty == 'easy' else HARD_PROMPT_FILE
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        prompts = [line.strip() for line in f if line.strip()]
    return prompts

def get_random_prompt(difficulty):
    prompts = load_prompts(difficulty)
    print(f"[DEBUG] Loaded {len(prompts)} prompts from {difficulty} file.")
    if not prompts:
        return "No prompts found."
    return random.choice(prompts)


def save_to_leaderboard(name, wpm, mistakes):
    with open(LEADERBOARD_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{name} - WPM: {wpm}, Mistakes: {mistakes}\n")
