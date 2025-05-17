# agents/mapping_loader.py

import json
import os

class MappingLoaderAgent:
    def __init__(self, mapping_path):
        self.mapping_path = mapping_path
        self._load()

    def _load(self):
        if os.path.exists(self.mapping_path):
            with open(self.mapping_path, 'r', encoding='utf-8') as f:
                self.mapping = json.load(f)
        else:
            self.mapping = []

    def get_all_targets(self):
        targets = []
        for entry in self.mapping:
            targets.extend(entry.get("targetPath", []))
        return list(set(targets))

    def get_targets_by_source(self, source_path):
        results = []
        for entry in self.mapping:
            if source_path in entry.get("sourcePath", []):
                results.extend(entry.get("targetPath", []))
        return list(set(results))

    def get_sources_by_target(self, target_path):
        results = []
        for entry in self.mapping:
            if target_path in entry.get("targetPath", []):
                results.extend(entry.get("sourcePath", []))
        return list(set(results))

    def reload(self):
        self._load()

    def get_mapping(self):
        return self.mapping