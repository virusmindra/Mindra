import json
import os
from typing import Dict, List

from config import DATA_DIR

MEMORY_FILE = os.path.join(DATA_DIR, "memories.json")
MAX_STORED_MEMORIES = 20

def load_memories() -> Dict[str, List[str]]:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
                if isinstance(data, dict):
                    # нормализуем ключи в строки и значения в список строк
                    normalized: Dict[str, List[str]] = {}
                    for key, value in data.items():
                        if isinstance(value, list):
                            normalized[str(key)] = [str(item) for item in value if str(item).strip()]
                        elif isinstance(value, str):
                            normalized[str(key)] = [value]
                    return normalized
            except json.JSONDecodeError:
                pass
    return {}

def save_memories(data: Dict[str, List[str]]) -> None:
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    cleaned: Dict[str, List[str]] = {}
    for key, value in data.items():
        if not value:
            continue
        cleaned[str(key)] = [str(item).strip() for item in value if str(item).strip()]
    with open(MEMORY_FILE, "w", encoding="utf-8") as fh:
        json.dump(cleaned, fh, ensure_ascii=False, indent=2)

def get_user_memories(memory_store: Dict[str, List[str]], user_id: str) -> List[str]:
    return memory_store.get(str(user_id), [])

def set_user_memories(memory_store: Dict[str, List[str]], user_id: str, memories: List[str]) -> None:
    normalized = []
    seen = set()
    for item in memories:
        text = str(item).strip()
        if not text:
            continue
        if text.lower() in seen:
            continue
        seen.add(text.lower())
        normalized.append(text)
        if len(normalized) >= MAX_STORED_MEMORIES:
            break
    memory_store[str(user_id)] = normalized

def append_user_memory(memory_store: Dict[str, List[str]], user_id: str, memory: str) -> None:
    if not memory:
        return
    existing = get_user_memories(memory_store, user_id)
    if memory.strip().lower() in {m.lower() for m in existing}:
        return
    updated = existing + [memory.strip()]
    set_user_memories(memory_store, user_id, updated)
