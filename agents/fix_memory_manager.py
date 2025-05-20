# fix_memory_manager.py

import json
import os

MEMORY_PATH = "logs/fix_memory.json"

class FixMemoryManager:
    def __init__(self):
        self.memory = self._load()

    def _load(self):
        if os.path.exists(MEMORY_PATH):
            with open(MEMORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save(self):
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2)

    def get_attempts(self, file_path):
        return self.memory.get(file_path, {}).get("attempted_strategies", [])

    def record_attempt(self, file_path, strategy):
        if file_path not in self.memory:
            self.memory[file_path] = {"attempted_strategies": []}
        if strategy not in self.memory[file_path]["attempted_strategies"]:
            self.memory[file_path]["attempted_strategies"].append(strategy)
        self.save()

    def reset(self, file_path):
        if file_path in self.memory:
            del self.memory[file_path]
            self.save()
