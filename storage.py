# storage.py

from collections import defaultdict

# Временное хранилище в памяти
user_goals = defaultdict(list)

def add_goal_for_user(user_id, goal_text):
    user_goals[user_id].append({"text": goal_text, "done": False})

def get_goals_for_user(user_id):
    return [g["text"] for g in user_goals.get(user_id, []) if not g["done"]]

def mark_goal_done(user_id, goal_text):
    for goal in user_goals.get(user_id, []):
        if goal["text"] == goal_text:
            goal["done"] = True
            return True
    return False
