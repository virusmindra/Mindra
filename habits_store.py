def mark_habit_done(uid: str, habit_id: str) -> bool:
    items = get_habits(uid)
    for h in items:
        if str(h.get("id")) == str(habit_id):
            h["doneToday"] = True
            h["lastDoneAt"] = int(time.time())
            _save(uid, items)
            return True
    return False
