# agents/file_name_class_name_validator.py

import os
import re
import json

MAPPING_PATH = "data/mapping.json"
MISMATCH_LOG_PATH = "logs/filename_mismatches.json"

class FileNameClassNameValidatorAgent:
    def __init__(self, migrated_dir):
        self.migrated_dir = migrated_dir
        self.mismatches = []

    def run(self):
        print("🔍 Running FileName-ClassName Validator...")
        self._load_mapping()
        self._scan_and_fix()
        self._save_mapping()
        self._log_results()

    def _load_mapping(self):
        if os.path.exists(MAPPING_PATH):
            with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
                self.mapping = json.load(f)
        else:
            self.mapping = []

    def _save_mapping(self):
        with open(MAPPING_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, indent=2)

    def _scan_and_fix(self):
        for root, _, files in os.walk(self.migrated_dir):
            for file in files:
                if file.endswith(".java"):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    match = re.search(r'public\s+class\s+(\w+)', content)
                    if match:
                        declared_class = match.group(1)
                        file_base = os.path.splitext(file)[0]
                        if declared_class != file_base:
                            self._fix(path, file, declared_class)

    def _fix(self, full_path, old_file_name, class_name):
        old_name = os.path.basename(full_path)
        dir_path = os.path.dirname(full_path)
        new_file_name = f"{class_name}.java"
        new_full_path = os.path.join(dir_path, new_file_name)

        os.rename(full_path, new_full_path)
        self._update_mapping(old_name, new_file_name)

        self.mismatches.append({
            "old_file": old_file_name,
            "new_file": new_file_name,
            "class_name": class_name
        })

    def _update_mapping(self, old_file, new_file):
        updated = False
        for entry in self.mapping:
            new_targets = []
            for path in entry.get("targetPath", []):
                if os.path.basename(path) == old_file:
                    path = path.replace(old_file, new_file)
                    updated = True
                new_targets.append(path)
            entry["targetPath"] = new_targets
        if not updated:
            print(f"⚠️  File {old_file} not found in mapping.json")

    def _log_results(self):
        if not self.mismatches:
            print("✅ No mismatches found.")
            return
        os.makedirs(os.path.dirname(MISMATCH_LOG_PATH), exist_ok=True)
        with open(MISMATCH_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.mismatches, f, indent=2)
        print(f"✅ Fixed {len(self.mismatches)} filename-classname mismatches. Logged to {MISMATCH_LOG_PATH}")
