# agents/relationship_builder.py

import os
import json
import javalang
from collections import defaultdict

class RelationshipBuilderAgent:
    def __init__(self, legacy_dir, migrated_dir, mapping_path, output_dir):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.mapping_path = mapping_path
        self.output_dir = output_dir
        self.mapping = self._load_mapping()
        self.index = {}

    def _load_mapping(self):
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _parse_class_and_methods(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            tree = javalang.parse.parse(code)
        except:
            return None, []

        class_name = None
        method_names = []
        for _, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
            if isinstance(node, javalang.tree.MethodDeclaration):
                method_names.append(node.name)
        return class_name, method_names

    def _find_all_migrated_classes(self):
        class_map = {}
        method_index = defaultdict(list)

        base_path = os.path.join(self.output_dir, 'src/main/java')
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith(".java"):
                    file_path = os.path.join(root, file)
                    class_name, methods = self._parse_class_and_methods(file_path)
                    if class_name:
                        fqcn = os.path.relpath(file_path, base_path).replace(os.sep, ".").replace(".java", "")
                        class_map[class_name] = fqcn
                        method_index[class_name].extend(methods)
        return class_map, method_index

    def _reverse_mapping(self):
        rev_map = defaultdict(list)
        for entry in self.mapping:
            targets = entry.get("targetPath", [])
            sources = entry.get("sourcePath", [])
            for tgt in targets:
                rev_map[tgt].extend(sources)
        return rev_map

    def _related_targets_by_source(self, target_path):
        related = set()
        for entry in self.mapping:
            if target_path in entry.get("targetPath", []):
                for tgt in entry.get("targetPath", []):
                    if tgt != target_path:
                        related.add(tgt)
        return list(related)

    def build(self):
        print("🔍 Building relationships for all migrated files...")
        class_map, method_index = self._find_all_migrated_classes()
        reverse_map = self._reverse_mapping()

        output_dir = os.path.join(self.output_dir, "relationships")
        os.makedirs(output_dir, exist_ok=True)

        for target_path in reverse_map:
            sources = reverse_map[target_path]
            related_targets = self._related_targets_by_source(target_path)

            relationship = {
                "targetPath": target_path,
                "legacySources": sources,
                "relatedMigratedTargets": related_targets,
                "classMap": class_map,
                "methodIndex": method_index
            }

            # Store as per target path name
            filename = os.path.basename(target_path).replace(".java", "") + "_relationship.json"
            out_path = os.path.join(output_dir, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(relationship, f, indent=2)

        print(f"✅ Relationship files written to: {output_dir}")
