import json
import os

MODES_PATH = "data/modes.json"

def load_user_modes():
    if os.path.exists(MODES_PATH):
        with open(MODES_PATH, "r") as f:
            return json.load(f)
    return {}

def save_user_modes(data):
    with open(MODES_PATH, "w") as f:
        json.dump(data, f)
