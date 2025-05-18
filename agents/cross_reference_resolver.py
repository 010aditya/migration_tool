# agents/cross_reference_resolver.py

import os
import re
import json
import javalang

class CrossReferenceResolverAgent:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.relationship_dir = os.path.join(output_dir, "relationships")

    def resolve_and_patch(self, target_file_path):
        full_path = os.path.join(self.output_dir, target_file_path)
        if not os.path.exists(full_path):
            print(f"❌ File not found for cross-reference resolution: {full_path}")
            return False

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            print(f"❌ Failed to read file {full_path}: {e}")
            return False

        relationship = self._load_relationship(target_file_path)
        class_map = relationship.get("classMap", {}) if relationship else {}

        # Step 1: Fix package declaration
        correct_package = self._infer_package_from_path(target_file_path)
        code = self._fix_package_declaration(code, correct_package)

        # Step 2: Extract undefined types
        undefined_types = self._extract_undefined_types(code)
        resolved_imports = self._resolve_imports(undefined_types, class_map)
        code = self._apply_imports(code, resolved_imports)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"✅ Cross-reference resolved: {target_file_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to write patched file {full_path}: {e}")
            return False

    def _load_relationship(self, target_path):
        filename = os.path.basename(target_path).replace(".java", "") + "_relationship.json"
        rel_path = os.path.join(self.relationship_dir, filename)
        if os.path.exists(rel_path):
            try:
                with open(rel_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error loading relationship for {target_path}: {e}")
        return None

    def _infer_package_from_path(self, relative_path):
        java_src_index = relative_path.find("src/main/java/")
        if java_src_index != -1:
            package_path = relative_path[java_src_index + len("src/main/java/" ):]
            package_dir = os.path.dirname(package_path)
            return package_dir.replace("/", ".").replace("\\", ".")
        return None

    def _fix_package_declaration(self, code, correct_package):
        if not correct_package:
            return code
        updated = False
        lines = code.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("package "):
                if correct_package not in line:
                    lines[i] = f"package {correct_package};"
                    updated = True
                break
        else:
            lines.insert(0, f"package {correct_package};")
            updated = True
        if updated:
            print(f"✅ Package declaration fixed: {correct_package}")
        return "\n".join(lines)

    def _extract_undefined_types(self, code):
        try:
            tree = javalang.parse.parse(code)
        except:
            return []
        defined_imports = set()
        if hasattr(tree, 'imports'):
            for imp in tree.imports:
                defined_imports.add(imp.path.split(".")[-1])
        defined_types = set()
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                defined_types.add(node.name)
        used_types = set(match.group(1) for match in re.finditer(r'\b([A-Z][a-zA-Z0-9_]*)\b', code))
        common_java_types = {'String', 'Integer', 'Long', 'List', 'Map', 'Boolean', 'Double'}
        undefined = used_types - defined_imports - defined_types - common_java_types
        return list(undefined)

    def _resolve_imports(self, type_names, class_map):
        resolved_imports = []
        for name in type_names:
            if name in class_map:
                resolved_imports.append(class_map[name])
        return resolved_imports

    def _apply_imports(self, code, import_fqns):
        lines = code.splitlines()
        import_lines = [f"import {fqcn};" for fqcn in sorted(set(import_fqns))]
        insert_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("package "):
                insert_index = i + 1
                break
        while insert_index < len(lines) and lines[insert_index].strip().startswith("import "):
            insert_index += 1
        lines = [line for line in lines if not line.strip().startswith("import ")]
        lines[insert_index:insert_index] = import_lines
        return "\n".join(lines)
