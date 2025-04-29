import os
import random
from pymongo import MongoClient

# ─── MongoDB setup ─────────────────────────────────────────────────────────
MONGO_URI   = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client      = MongoClient(MONGO_URI)
db          = client["typing_test"]
prompts_col = db["prompts"]

# ─── Leaderboard file (unchanged) ───────────────────────────────────────────
LEADERBOARD_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "files",
    "leaderboard.txt"
)

# ─── Prompt-loading functions ───────────────────────────────────────────────
def load_prompts(difficulty):
    """
    Return a list of all 'text' fields for documents
    in the 'prompts' collection matching the given difficulty.
    """
    return [doc["text"] for doc in prompts_col.find({"difficulty": difficulty})]

def get_random_prompt(difficulty):
    """
    Pick one prompt at random (or fallback text if empty).
    """
    arr = load_prompts(difficulty)
    return random.choice(arr) if arr else "No prompts found."

# ─── Leaderboard-writing function ───────────────────────────────────────────def save_to_leaderboard(name, wpm, mistakes, difficulty):
    with open(LEADERBOARD_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{difficulty.capitalize()} - {name} - WPM: {wpm}, Mistakes: {mistakes}\n")
