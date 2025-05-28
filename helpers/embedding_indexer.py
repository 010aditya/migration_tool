import os
import json
import numpy as np
from langchain_openai import AzureOpenAIEmbeddings

# ---- CONFIG ----
AZURE_OPENAI_API_KEY = "YOUR_AZURE_API_KEY"
AZURE_OPENAI_ENDPOINT = "YOUR_AZURE_ENDPOINT"
EMBEDDING_DEPLOYMENT = "YOUR_EMBEDDING_DEPLOYMENT"
AZURE_API_VERSION = "2024-04-01-preview"
MIGRATED_DIR = "migrated_code/"
LEGACY_DIR = "legacy_code/"
OUTPUT_PATH = "data/embedding_index.json"

embeddings = AzureOpenAIEmbeddings(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name=EMBEDDING_DEPLOYMENT,
    api_version=AZURE_API_VERSION
)

def index_code_files(code_dir, tag):
    index = []
    for root, dirs, files in os.walk(code_dir):
        for file in files:
            if file.endswith(".java"):
                path = os.path.join(root, file)
                name = os.path.splitext(file)[0]
                with open(path, encoding="utf-8") as f:
                    code = f.read()
                embedding = embeddings.embed_query(code)
                index.append({
                    "tag": tag,
                    "file": path,
                    "class": name,
                    "embedding": embedding
                })
    return index

def main():
    index = []
    print("Indexing migrated code...")
    index += index_code_files(MIGRATED_DIR, "migrated")
    print("Indexing legacy code...")
    index += index_code_files(LEGACY_DIR, "legacy")
    # Save as JSON (embeddings as lists for JSON)
    for entry in index:
        entry["embedding"] = list(entry["embedding"])
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"Saved embeddings to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()


# Example to load below

# import numpy as np
# import json

# def load_embedding_index(path):
#     with open(path, "r", encoding="utf-8") as f:
#         index = json.load(f)
#     for entry in index:
#         entry["embedding"] = np.array(entry["embedding"])
#     return index

# def find_best_embedding_match(query_code, index, tag=None, top_k=1):
#     query_emb = embeddings.embed_query(query_code)
#     candidates = index if not tag else [e for e in index if e["tag"] == tag]
#     scores = [(float(np.dot(query_emb, e["embedding"]) / (np.linalg.norm(query_emb) * np.linalg.norm(e["embedding"]))), e) for e in candidates]
#     scores.sort(reverse=True, key=lambda x: x[0])
#     return [e for s, e in scores[:top_k] if s > 0.75]
