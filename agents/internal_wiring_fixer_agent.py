import os
import re
import json
import numpy as np
from src.utils.embedding_utils import get_embedder, cosine_similarity

class InternalWiringFixerAgent:
    def __init__(self,
                 migrated_dir,
                 embedding_index_path,
                 legacy_embedding_index_path,
                 legacy_dir,
                 reporter,
                 similarity_threshold=0.7,
                 legacy_threshold=0.75):
        self.migrated_dir = migrated_dir
        self.legacy_dir = legacy_dir
        self.similarity_threshold = similarity_threshold
        self.legacy_threshold = legacy_threshold
        self.embedder = get_embedder()
        self.reporter = reporter

        # Load migrated and legacy embeddings
        with open(embedding_index_path, "r", encoding="utf-8") as f:
            self.embedding_index = json.load(f)
        with open(legacy_embedding_index_path, "r", encoding="utf-8") as f:
            self.legacy_embedding_index = json.load(f)

        self.migrated_classnames = {os.path.splitext(os.path.basename(fp))[0]: fp for fp in self.embedding_index}
        self.legacy_classnames = {os.path.splitext(os.path.basename(fp))[0]: fp for fp in self.legacy_embedding_index}

    def recursive_fix(self, max_passes=10):
        for i in range(max_passes):
            print(f"\n--- InternalWiringFixerAgent Pass {i+1} ---")
            num_changes = self.scan_and_fix_all()
            print(f"Pass {i+1}: {num_changes} rewires/ports applied.")
            if num_changes == 0:
                print("No more changes detected. Wiring is stable.")
                break
        else:
            print("Warning: Max recursion reached; unresolved references may remain.")

    def scan_and_fix_all(self):
        total_changes = 0
        for root, _, files in os.walk(self.migrated_dir):
            for file in files:
                if file.endswith('.java'):
                    total_changes += self.scan_and_fix_file(os.path.join(root, file))
        return total_changes

    def scan_and_fix_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        changed = 0

        # Pattern-driven rewiring
        patterns = [
            # (pattern, match_type, class_index, format_original, format_new)
            (r'@(Autowired|Resource|Mock)\s+private\s+(\w+)\s+(\w+);', 'field_injection', 2,
             lambda m: f"@{m[1]} private {m[2]} {m[3]};",
             lambda m, c: f"@{m[1]} private {c} {m[3]};"),
            (r'new\s+(\w+)\s*\(', 'instantiation', 1,
             lambda m: f"new {m[1]}(",
             lambda m, c: f"new {c}("),
            (r'import\s+[\w\.]+(\w+);', 'import', 1,
             lambda m: f"import ...{m[1]};",
             lambda m, c: f"import ...{c};"),
            (r'<(\w+)>', 'generic_type', 1,
             lambda m: f"<{m[1]}>",
             lambda m, c: f"<{c}>"),
            (r'(implements|extends)\s+(\w+)', 'implements_extends', 2,
             lambda m: f"{m[1]} {m[2]}",
             lambda m, c: f"{m[1]} {c}"),
            (r'@\w+\((\w+)\.class\)', 'annotation_class_param', 1,
             lambda m: f"@...({m[1]}.class)",
             lambda m, c: f"@...({c}.class)"),
            (r'throws\s+(\w+)', 'throws_clause', 1,
             lambda m: f"throws {m[1]}",
             lambda m, c: f"throws {c}"),
            (r'catch\s*\(\s*(\w+)\s+\w+\s*\)', 'catch_clause', 1,
             lambda m: f"catch ({m[1]} ...)",
             lambda m, c: f"catch ({c} ...)"),
            (r'(\w+)::\w+', 'method_reference', 1,
             lambda m: f"{m[1]}::...",
             lambda m, c: f"{c}::..."),
            (r'Class\.forName\(\"[\w\.]*?(\w+)\"\)', 'class_forname', 1,
             lambda m: f'Class.forName("...{m[1]}")',
             lambda m, c: f'Class.forName("...{c}")'),
            (r'@(\w+)\b', 'annotation_usage', 1,
             lambda m: f"@{m[1]}",
             lambda m, c: f"@{c}"),
            (r'@Resource\s*\(name\s*=\s*\"(\w+)\"\)', 'resource_name', 1,
             lambda m: f'@Resource(name="{m[1]}")',
             lambda m, c: f'@Resource(name="{c}")')
        ]

        for pattern, match_type, class_index, format_original, format_new in patterns:
            changed += self._rewire_pattern(
                code, file_path, pattern, match_type, class_index, format_original, format_new
            )

        # Constructor injection (handled separately)
        changed += self._rewire_constructor_injection(code, file_path)

        # Write file if changed
        if changed:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        return changed

    def _rewire_pattern(self, code, file_path, pattern, match_type, class_index, format_original, format_new):
        changed = 0
        matches = list(re.finditer(pattern, code))
        for match in matches:
            target_class = match[class_index]
            # Try migrated code first
            if target_class in self.migrated_classnames:
                continue
            candidate, score = self.find_best_internal_match(target_class)
            if candidate and score > self.similarity_threshold:
                original = format_original(match)
                new = format_new(match, candidate)
                code, n = re.subn(re.escape(original), new, code)
                if n > 0:
                    changed += n
                    self.reporter.log_rewire(
                        file_path=file_path,
                        original=original,
                        new=new,
                        rewire_type=match_type,
                        reason="embedding_match",
                        confidence="high" if score > 0.8 else "medium",
                        similarity_score=score
                    )
            else:
                # Try legacy as fallback
                legacy_candidate, legacy_score = self.find_best_legacy_match(target_class)
                if legacy_candidate and legacy_score > self.legacy_threshold:
                    self.port_legacy_class(legacy_candidate)
                    original = format_original(match)
                    new = format_new(match, legacy_candidate)
                    code, n = re.subn(re.escape(original), new, code)
                    if n > 0:
                        changed += n
                        self.reporter.log_rewire(
                            file_path=file_path,
                            original=original,
                            new=new,
                            rewire_type=f"{match_type}_ported",
                            reason="ported_from_legacy",
                            confidence="medium" if legacy_score > 0.8 else "low",
                            similarity_score=legacy_score
                        )
                else:
                    self.reporter.log_rewire(
                        file_path=file_path,
                        original=format_original(match),
                        new=None,
                        rewire_type=f"unresolved_{match_type}",
                        reason="no_good_match_anywhere",
                        confidence="none"
                    )
        return changed

    def _rewire_constructor_injection(self, code, file_path):
        changed = 0
        ctor_pattern = r'public\s+\w+\s*\(([^\)]*)\)'
        for ctor_match in re.finditer(ctor_pattern, code):
            param_list = ctor_match.group(1)
            params = [p.strip() for p in param_list.split(",") if p.strip()]
            for param in params:
                parts = param.split()
                if len(parts) == 2:
                    param_type, param_var = parts
                    if param_type in self.migrated_classnames:
                        continue
                    candidate, score = self.find_best_internal_match(param_type)
                    if candidate and score > self.similarity_threshold:
                        pattern = rf'\b{param_type}\s+{param_var}\b'
                        code, n = re.subn(pattern, f"{candidate} {param_var}", code)
                        if n > 0:
                            changed += n
                            self.reporter.log_rewire(
                                file_path=file_path,
                                original=f"{param_type} {param_var}",
                                new=f"{candidate} {param_var}",
                                rewire_type="constructor_injection",
                                reason="embedding_match",
                                confidence="high" if score > 0.8 else "medium",
                                similarity_score=score
                            )
                    else:
                        legacy_candidate, legacy_score = self.find_best_legacy_match(param_type)
                        if legacy_candidate and legacy_score > self.legacy_threshold:
                            self.port_legacy_class(legacy_candidate)
                            pattern = rf'\b{param_type}\s+{param_var}\b'
                            code, n = re.subn(pattern, f"{legacy_candidate} {param_var}", code)
                            if n > 0:
                                changed += n
                                self.reporter.log_rewire(
                                    file_path=file_path,
                                    original=f"{param_type} {param_var}",
                                    new=f"{legacy_candidate} {param_var}",
                                    rewire_type="constructor_injection_ported",
                                    reason="ported_from_legacy",
                                    confidence="medium" if legacy_score > 0.8 else "low",
                                    similarity_score=legacy_score
                                )
                        else:
                            self.reporter.log_rewire(
                                file_path=file_path,
                                original=f"{param_type} {param_var}",
                                new=None,
                                rewire_type="unresolved_constructor_injection",
                                reason="no_good_match_anywhere",
                                confidence="none"
                            )
        return changed

    def find_best_internal_match(self, query_class_name):
        dummy_code = f"public class {query_class_name} {{}}"
        query_vec = np.array(self.embedder.embed_documents([dummy_code])[0])
        best_score = -1.0
        best_class = None
        for migrated_class, file_path in self.migrated_classnames.items():
            vec = np.array(self.embedding_index[file_path])
            score = cosine_similarity(query_vec, vec)
            if score > best_score:
                best_score = score
                best_class = migrated_class
        return best_class, best_score

    def find_best_legacy_match(self, query_class_name):
        dummy_code = f"public class {query_class_name} {{}}"
        query_vec = np.array(self.embedder.embed_documents([dummy_code])[0])
        best_score = -1.0
        best_class = None
        for legacy_class, file_path in self.legacy_classnames.items():
            vec = np.array(self.legacy_embedding_index[file_path])
            score = cosine_similarity(query_vec, vec)
            if score > best_score:
                best_score = score
                best_class = legacy_class
        return best_class, best_score

    def port_legacy_class(self, class_name):
        src_path = self.legacy_embedding_index[self.legacy_classnames[class_name]]
        dest_dir = self.migrated_dir
        rel_path = os.path.relpath(src_path, self.legacy_dir)
        target_path = os.path.join(dest_dir, rel_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(src_path, "r", encoding="utf-8") as src, open(target_path, "w", encoding="utf-8") as dest:
            code = src.read()
            code = "// [LEGACY-PORTED: review needed]\n" + code
            dest.write(code)
        print(f"Ported legacy class: {src_path} -> {target_path}")
        self.reporter.log_rewire(
            file_path=target_path,
            original=src_path,
            new=target_path,
            rewire_type="legacy_class_ported",
            reason="legacy_needed_for_wiring"
        )


# from src.reporting.migration_reporter import MigrationReporter
# from src.agents.internal_wiring_fixer_agent import InternalWiringFixerAgent

# reporter = MigrationReporter(output_path="data/migration_report.json")
# agent = InternalWiringFixerAgent(
#     migrated_dir="migrated_code/",
#     embedding_index_path="data/embedding_index.json",
#     legacy_embedding_index_path="data/legacy_embedding_index.json",
#     legacy_dir="legacy_code/",
#     reporter=reporter,
#     similarity_threshold=0.7,
#     legacy_threshold=0.75
# )
# agent.recursive_fix(max_passes=10)
# reporter.write_report()
