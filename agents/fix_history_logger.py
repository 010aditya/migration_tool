# agents/fix_history_logger.py

import os
import json

class FixHistoryLogger:
    def __init__(self, log_dir="logs/fix_history"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def log(self, target_path, result):
        file_name = os.path.basename(target_path)
        log_path = os.path.join(self.log_dir, f"{file_name}.json")

        history_entry = {
            "file": target_path,
            "fix_log": result.get("fix_log", {}),
            "success": result.get("success", False),
            "generated_code": result.get("fixed_code", "")
        }

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(history_entry, f, indent=2)

        print(f"📝 Fix history logged for {target_path} → {log_path}")