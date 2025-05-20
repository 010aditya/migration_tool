import os
import javalang
import difflib
from utils.accurate_class_indexer import AccurateClassIndexer

class CrossReferenceResolverAgent:
    def __init__(self, migrated_dir, class_index):
        self.migrated_dir = migrated_dir
        self.class_index = class_index  # AccurateClassIndexer instance

    def resolve(self, target_path):
        file_path = os.path.join(self.migrated_dir, target_path)
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        try:
            tree = javalang.parse.parse(code)
        except Exception as e:
            print(f"❌ Failed to parse {target_path}: {e}")
            return

        # Extract imports and types used
        imports = [imp.path for imp in tree.imports]
        type_refs = self._extract_type_references(tree)
        defined_types = [t.name for t in tree.types if hasattr(t, 'name')]

        undefined_types = [t for t in type_refs if t not in imports and t not in defined_types and not self._is_java_builtin(t)]
        corrections = {}

        for t in undefined_types:
            best_match = difflib.get_close_matches(t, self.class_index.index.keys(), n=1, cutoff=0.7)
            if best_match:
                match = best_match[0]
                full_path = self.class_index.resolve(match)
                if full_path:
                    package = full_path.replace("/", ".").rsplit(".java", 1)[0]
                    corrections[t] = (match, f"import {package};")

        updated_code = self._apply_fixes(code, corrections)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_code)

        print(f"✅ Cross-reference resolved for {target_path}: {list(corrections.keys())}")

    def _extract_type_references(self, tree):
        refs = set()
        for path, node in tree.filter(javalang.tree.ReferenceType):
            if isinstance(node.name, str):
                refs.add(node.name)
        return refs

    def _is_java_builtin(self, name):
        java_builtins = {'String', 'List', 'Map', 'Integer', 'Boolean', 'Object'}
        return name in java_builtins

    def _apply_fixes(self, code, corrections):
        lines = code.splitlines()
        new_lines = []
        inserted_imports = set()

        for line in lines:
            new_line = line
            for original, (replacement, _) in corrections.items():
                if original in new_line:
                    new_line = new_line.replace(original, replacement)
            new_lines.append(new_line)

        # Preserve existing imports
        existing_imports = [line for line in lines if line.strip().startswith("import ")]

        # Add new imports
        for _, (_, import_stmt) in corrections.items():
            if import_stmt not in existing_imports:
                inserted_imports.add(import_stmt)

        # Insert imports after package
        final_lines = []
        package_inserted = False
        for line in new_lines:
            final_lines.append(line)
            if not package_inserted and line.strip().startswith("package"):
                final_lines.extend(sorted(inserted_imports))
                package_inserted = True

        return "\n".join(final_lines)
