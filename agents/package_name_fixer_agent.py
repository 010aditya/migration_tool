# agents/package_name_fixer_agent.py

import os

class PackageNameFixerAgent:
    def __init__(self, migrated_dir):
        self.migrated_dir = migrated_dir

    def fix(self, relative_path):
        full_path = os.path.join(self.migrated_dir, relative_path)
        if not os.path.exists(full_path):
            print(f"❌ File not found for package fix: {full_path}")
            return False

        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Infer correct package from path
        java_src_root = os.path.join(self.migrated_dir, "src", "main", "java")
        if not full_path.startswith(java_src_root):
            print("⚠️ File path does not match src/main/java structure")
            return False

        relative = os.path.relpath(full_path, java_src_root)
        package_path = os.path.dirname(relative).replace(os.sep, ".")
        expected_package = f"package {package_path};"

        found_package = False
        for i, line in enumerate(lines):
            if line.strip().startswith("package "):
                found_package = True
                if line.strip() != expected_package:
                    print(f"🔧 Fixing package declaration: {line.strip()} → {expected_package}")
                    lines[i] = expected_package + "\n"
                break

        if not found_package:
            # Insert package on top
            print(f"➕ Adding package declaration: {expected_package}")
            lines.insert(0, expected_package + "\n\n")

        with open(full_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
