# agents/circular_dependency_detector.py

import os
import re
from collections import defaultdict

class CircularDependencyDetectorAgent:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.dependency_graph = defaultdict(set)

    def _collect_java_files(self):
        java_files = []
        for root, _, files in os.walk(self.project_dir):
            for f in files:
                if f.endswith(".java"):
                    java_files.append(os.path.join(root, f))
        return java_files

    def _extract_class_and_dependencies(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        package_match = re.search(r'package\s+([\w\.]+);', code)
        class_match = re.search(r'(public\s+)?(class|interface)\s+(\w+)', code)
        if not class_match:
            return None, []

        full_class_name = class_match.group(3)
        if package_match:
            full_class_name = f"{package_match.group(1)}.{full_class_name}"

        dependencies = re.findall(r'(private|protected|public)?\s+(\w+)\s+\w+;', code)
        referenced_classes = [cls for _, cls in dependencies if cls[0].isupper()]
        return full_class_name, referenced_classes

    def detect_cycles(self):
        files = self._collect_java_files()

        for file in files:
            source_class, deps = self._extract_class_and_dependencies(file)
            if source_class:
                for dep in deps:
                    self.dependency_graph[source_class].add(dep)

        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    cycles.append((node, neighbor))
                    return True
            rec_stack.remove(node)
            return False

        for class_name in self.dependency_graph:
            if class_name not in visited:
                dfs(class_name)

        if cycles:
            print("❌ Circular dependencies detected:")
            for a, b in cycles:
                print(f" - {a} ↔ {b}")
        else:
            print("✅ No circular dependencies detected.")

        return cycles
