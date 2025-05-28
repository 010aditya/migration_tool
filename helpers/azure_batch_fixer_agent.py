import os
import json
import javalang
import re
import numpy as np
from langchain_openai import AzureChatOpenAI

# ---- CONFIG ----
AZURE_OPENAI_API_KEY = "YOUR_AZURE_API_KEY"
AZURE_OPENAI_ENDPOINT = "YOUR_AZURE_ENDPOINT"
GPT_DEPLOYMENT = "YOUR_GPT_DEPLOYMENT"
AZURE_API_VERSION = "2024-04-01-preview"

MAPPING_JSON = "data/mapping.json"
RELATIONSHIP_JSON = "data/legacy_relationships.json"
BUILD_LOG_PATH = "data/build.log"
EMBEDDING_INDEX_PATH = "data/embedding_index.json"
LEGACY_DIR = "legacy_code/"
MIGRATED_DIR = "migrated_code/"
PROMPT_PATH = "prompts/llm_patch_prompt.txt"
BATCH_SIZE = 5
REL_BATCH_SIZE = 3
STUB_PACKAGE = "com.stub"
AUDIT_LOG = "data/azure_batch_fixer_audit_log.json"

llm = AzureChatOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name=GPT_DEPLOYMENT,
    api_version=AZURE_API_VERSION
)

# ---- UTILS ----

def get_class_name_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]

def load_mapping(mapping_path):
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    legacy_to_migrated, migrated_to_legacy = {}, {}
    for entry in mapping:
        for src_path in entry["source"]:
            src_class = get_class_name_from_path(src_path)
            tgt_classes = [get_class_name_from_path(p) for p in entry["target"]]
            legacy_to_migrated.setdefault(src_class, []).extend(tgt_classes)
            for tgt_class in tgt_classes:
                migrated_to_legacy.setdefault(tgt_class, []).append(src_class)
    return legacy_to_migrated, migrated_to_legacy

def parse_build_log(build_log_path):
    broken_classes = set()
    with open(build_log_path, encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "error: cannot find symbol" in line:
            for j in range(1, 3):
                if i + j < len(lines) and "class" in lines[i + j]:
                    parts = lines[i + j].strip().split()
                    if len(parts) >= 3:
                        broken_classes.add(parts[-1])
    return list(broken_classes)

def load_relationships(relationship_path):
    with open(relationship_path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_migrated_class_file(migrated_dir, migrated_class_name):
    for root, dirs, files in os.walk(migrated_dir):
        for file in files:
            if file == f"{migrated_class_name}.java":
                return os.path.join(root, file)
    return None

def read_java_code(file_path):
    if not file_path or not os.path.exists(file_path):
        return ""
    with open(file_path, encoding="utf-8") as f:
        return f.read()

def write_java_code(file_path, code):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

def generate_class_stub(class_name, package_name, output_dir):
    stub = f"package {package_name};\n\npublic class {class_name} {{\n    // TODO: Implement\n}}\n"
    os.makedirs(output_dir, exist_ok=True)
    stub_file = os.path.join(output_dir, f"{class_name}.java")
    with open(stub_file, "w", encoding="utf-8") as f:
        f.write(stub)
    return stub_file

def load_embedding_index(path):
    import numpy as np
    with open(path, "r", encoding="utf-8") as f:
        index = json.load(f)
    for entry in index:
        entry["embedding"] = np.array(entry["embedding"])
    return index

def cosine_sim(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def best_embedding_match(query_code, index, tag=None, top_k=1):
    from langchain_openai import AzureOpenAIEmbeddings
    embeddings = AzureOpenAIEmbeddings(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        deployment_name="YOUR_EMBEDDING_DEPLOYMENT",
        api_version=AZURE_API_VERSION
    )
    query_emb = np.array(embeddings.embed_query(query_code))
    candidates = index if not tag else [e for e in index if e["tag"] == tag]
    scores = [(cosine_sim(query_emb, e["embedding"]), e) for e in candidates]
    scores.sort(reverse=True, key=lambda x: x[0])
    return [e for s, e in scores[:top_k] if s > 0.75]

def load_prompt_template(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def prompt_patch_code(legacy_code, migrated_code, build_error, rel_codes, prompt_template):
    prompt = prompt_template.format(
        legacy_code=legacy_code or "",
        migrated_code=migrated_code or "",
        rel_codes=rel_codes or "",
        build_error=build_error or ""
    )
    return llm.invoke(prompt).content.strip()

# ---- MAIN AGENT ----

class AzureBatchFixerAgent:
    def __init__(
        self,
        legacy_dir,
        migrated_dir,
        mapping_json,
        relationship_json,
        build_log_path,
        embedding_index_path,
        prompt_path,
        batch_size=5,
        rel_batch_size=3,
        stub_package="com.stub",
        audit_log=AUDIT_LOG
    ):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.mapping_json = mapping_json
        self.relationship_json = relationship_json
        self.build_log_path = build_log_path
        self.embedding_index_path = embedding_index_path
        self.prompt_template = load_prompt_template(prompt_path)
        self.batch_size = batch_size
        self.rel_batch_size = rel_batch_size
        self.stub_package = stub_package
        self.audit_log_path = audit_log
        self.audit_log = []

        self.legacy_to_migrated, self.migrated_to_legacy = load_mapping(self.mapping_json)
        self.relationships = load_relationships(self.relationship_json)
        self.embedding_index = load_embedding_index(self.embedding_index_path)
        self.broken_classes = parse_build_log(self.build_log_path)

    def run(self):
        total = len(self.broken_classes)
        for i in range(0, total, self.batch_size):
            class_batch = self.broken_classes[i:i+self.batch_size]
            print(f"\nProcessing class batch: {class_batch}")
            for cls in class_batch:
                legacy_class = self.migrated_to_legacy.get(cls, [cls])[0]
                related = self.relationships.get(legacy_class, [])
                for j in range(0, len(related), self.rel_batch_size):
                    rel_batch = related[j:j+self.rel_batch_size]
                    print(f"  Fixing {cls} for relationships: {rel_batch}")
                    self.fix_class_relationships(cls, legacy_class, rel_batch)
        # Write audit log at the end
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(self.audit_log, f, indent=2)
        print(f"Audit log written to {self.audit_log_path}")

    def fix_class_relationships(self, migrated_class, legacy_class, rel_batch):
        migrated_class_file = find_migrated_class_file(self.migrated_dir, migrated_class)
        migrated_code = read_java_code(migrated_class_file)
        legacy_code = ""
        legacy_class_file = None
        for root, dirs, files in os.walk(self.legacy_dir):
            for file in files:
                if file.startswith(legacy_class) and file.endswith(".java"):
                    legacy_class_file = os.path.join(root, file)
                    legacy_code = read_java_code(legacy_class_file)
        rel_codes = []
        build_error = f"Class {migrated_class} has missing dependencies: {rel_batch}"
        for rel in rel_batch:
            # Use embedding match for best migrated candidate for rel
            candidates = [e for e in self.embedding_index if e["class"] == rel and e["tag"] == "migrated"]
            if not candidates:
                # Class stub if needed
                stub_file = generate_class_stub(rel, self.stub_package, os.path.join(self.migrated_dir, "stub"))
                rel_codes.append(read_java_code(stub_file))
                self.audit_log.append({
                    "fix_type": "class_stub",
                    "class": rel,
                    "file": stub_file
                })
            else:
                best = candidates[0]
                rel_codes.append(read_java_code(best["file"]))
        # GPT-4o Patch
        rel_context = "\n\n".join(rel_codes)
        revised_code = prompt_patch_code(legacy_code, migrated_code, build_error, rel_context, self.prompt_template)
        if revised_code.strip() and (revised_code.strip() != migrated_code.strip()):
            write_java_code(migrated_class_file, revised_code)
            self.audit_log.append({
                "fix_type": "llm_patch",
                "migrated_class": migrated_class,
                "file": migrated_class_file,
                "patched_code_snippet": revised_code[:500]  # log snippet for audit
            })
        else:
            self.audit_log.append({
                "fix_type": "noop",
                "migrated_class": migrated_class,
                "reason": "No patch needed or GPT returned unchanged code"
            })

# ---- USAGE ----

if __name__ == "__main__":
    agent = AzureBatchFixerAgent(
        legacy_dir=LEGACY_DIR,
        migrated_dir=MIGRATED_DIR,
        mapping_json=MAPPING_JSON,
        relationship_json=RELATIONSHIP_JSON,
        build_log_path=BUILD_LOG_PATH,
        embedding_index_path=EMBEDDING_INDEX_PATH,
        prompt_path=PROMPT_PATH,
        batch_size=BATCH_SIZE,
        rel_batch_size=REL_BATCH_SIZE,
        stub_package=STUB_PACKAGE
    )
    agent.run()


# prmpt sample

# You are a senior Java developer. Given:

# Legacy class/method (if any):
# ```java
# {legacy_code}
# Migrated class (with build error):

# java
# Copy
# Edit
# {migrated_code}
# Related classes/methods:

# java
# Copy
# Edit
# {rel_codes}
# Build error:
# {build_error}

# Instructions:

# Patch the migrated code to resolve the error using best practices.

# If a method or field is missing, inject/import/port as needed.

# If a type conversion is needed, fix it.

# Keep the code minimal and idiomatic Spring Boot.

# Respond with only the revised code block.