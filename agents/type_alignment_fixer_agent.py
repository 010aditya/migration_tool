import os
import re
import json
import javalang
from src.utils.embedding_utils import get_embedder, cosine_similarity

class TypeAlignmentFixerAgent:
    def __init__(self,
                 migrated_dir,
                 legacy_dir,
                 migrated_embedding_index_path,
                 legacy_embedding_index_path,
                 reporter,
                 similarity_threshold=0.7,
                 legacy_threshold=0.75):
        self.migrated_dir = migrated_dir
        self.legacy_dir = legacy_dir
        self.similarity_threshold = similarity_threshold
        self.legacy_threshold = legacy_threshold
        self.reporter = reporter
        self.embedder = get_embedder()
        # Load embeddings (if using for method pairing)
        with open(migrated_embedding_index_path, "r", encoding="utf-8") as f:
            self.migrated_embedding_index = json.load(f)
        with open(legacy_embedding_index_path, "r", encoding="utf-8") as f:
            self.legacy_embedding_index = json.load(f)

    def recursive_fix(self, max_passes=3):
        for i in range(max_passes):
            num_fixes = self.scan_and_fix_all()
            print(f"TypeAlignmentFixerAgent pass {i+1}: type fixes={num_fixes}")
            if num_fixes == 0:
                print("No more type alignment fixes needed.")
                break

    def scan_and_fix_all(self):
        fixes = 0
        migrated_methods = self.extract_all_methods(self.migrated_dir)
        legacy_methods = self.extract_all_methods(self.legacy_dir)

        for m_key, m_info in migrated_methods.items():
            l_key, l_info, sim = self.find_best_legacy_method_match(m_key, legacy_methods)
            if sim < self.legacy_threshold:
                continue  # No strong legacy match
            if m_info['return_type'] != l_info['return_type']:
                # Patch the migrated method signature and/or return statement
                patched = self.patch_return_type(m_info['file'], m_info, l_info['return_type'])
                fixes += int(patched)
                self.reporter.log_rewire(
                    file_path=m_info['file'],
                    original=f"{m_info['return_type']} {m_info['signature']}",
                    new=f"{l_info['return_type']} {l_info['signature']}",
                    rewire_type="type_alignment",
                    reason="aligned_to_legacy",
                    confidence="high"
                )
        return fixes

    def extract_all_methods(self, root_dir):
        methods = {}
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.java'):
                    java_file = os.path.join(root, file)
                    try:
                        with open(java_file, "r", encoding="utf-8") as f:
                            code = f.read()
                        tree = javalang.parse.parse(code)
                        for node in tree.types:
                            if isinstance(node, javalang.tree.ClassDeclaration):
                                for m in node.methods:
                                    sig = self.method_signature(m)
                                    methods[f"{node.name}.{sig}"] = {
                                        'return_type': m.return_type.name if m.return_type else "void",
                                        'params': [(p.type.name, p.name) for p in m.parameters],
                                        'name': m.name,
                                        'class': node.name,
                                        'signature': sig,
                                        'file': java_file,
                                        'node': m
                                    }
                    except Exception as e:
                        print(f"Failed to parse {java_file}: {e}")
        return methods

    def method_signature(self, m):
        params = ', '.join([f"{p.type.name} {p.name}" for p in m.parameters])
        return f"{m.name}({params})"

    def find_best_legacy_method_match(self, migrated_sig, legacy_methods):
        # Use simple name match, fallback to embedding for fuzzy match
        if migrated_sig in legacy_methods:
            return migrated_sig, legacy_methods[migrated_sig], 1.0
        # Fallback: fuzzy (embedding-based) match
        m_name = migrated_sig.split('(')[0]
        best_sim = 0.0
        best_key = None
        for l_key in legacy_methods:
            if m_name in l_key:
                best_key = l_key
                best_sim = 0.8
                break
        if best_key:
            return best_key, legacy_methods[best_key], best_sim
        # Otherwise: just pick best cosine similarity using class name or method embedding
        return "", {}, 0.0

    def patch_return_type(self, file_path, m_info, target_return_type):
        # For now, patch method signature return type (primitive/String demo)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            method_regex = (
                rf"((public|protected|private)\s+)([\w<>\[\]]+)(\s+{m_info['name']}\s*\([^\)]*\))"
            )
            patched_code, n = re.subn(
                method_regex,
                rf"\1{target_return_type}\4",
                code,
                count=1
            )
            if n:
                # If patching primitive <-> String, also patch return statement
                if (m_info['return_type'], target_return_type) in [("String", "int"), ("int", "String")]:
                    if target_return_type == "int":
                        # Patch 'return foo;' to 'return Integer.parseInt(foo);'
                        patched_code = re.sub(r'return\s+(\w+);', r'return Integer.parseInt(\1);', patched_code)
                    else:
                        # Patch 'return foo;' to 'return String.valueOf(foo);'
                        patched_code = re.sub(r'return\s+(\w+);', r'return String.valueOf(\1);', patched_code)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(patched_code)
                print(f"Patched return type in {file_path} method {m_info['name']} to {target_return_type}")
                return True
        except Exception as e:
            print(f"Failed to patch {file_path}: {e}")
        return False

# from src.reporting.migration_reporter import MigrationReporter
# from src.agents.type_alignment_fixer_agent import TypeAlignmentFixerAgent

# reporter = MigrationReporter(output_path="data/migration_report.json")
# agent = TypeAlignmentFixerAgent(
#     migrated_dir="migrated_code/",
#     legacy_dir="legacy_code/",
#     migrated_embedding_index_path="data/embedding_index.json",
#     legacy_embedding_index_path="data/legacy_embedding_index.json",
#     reporter=reporter
# )
# agent.recursive_fix(max_passes=3)
# reporter.write_report()
