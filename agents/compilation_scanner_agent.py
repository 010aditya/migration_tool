import os
import subprocess
import json

class CompilationScannerAgent:
    def __init__(self, source_root="output/fixed_codebase/src/main/java", log_dir="logs"):
        self.source_root = source_root
        self.log_path = os.path.join(log_dir, "compilation_report.json")
        os.makedirs(log_dir, exist_ok=True)

    def scan(self):
        report = {}

        for root, _, files in os.walk(self.source_root):
            for file in files:
                if file.endswith(".java"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.source_root)

                    # Attempt to compile this file
                    cmd = ["javac", full_path]
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode != 0:
                        report[rel_path] = result.stderr.strip()

        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"✅ Compilation report saved to {self.log_path}")
        return report

# Integration in main.py (add this to the end of the migrate_all block):
# from agents.compilation_scanner_agent import CompilationScannerAgent
# ...
# if args.migrate_all:
#     ...
#     print("\n🔎 Scanning individual files for compilation errors...")
#     scanner = CompilationScannerAgent(source_root=os.path.join(OUTPUT_DIR, "src/main/java"))
#     scanner.scan()
