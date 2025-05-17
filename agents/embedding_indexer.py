# agents/embedding_indexer.py

import os
import json
from sentence_transformers import SentenceTransformer
from llm.markdown_utils import clean_markdown_code

INDEX_PATH = "data/embedding_index.json"

class EmbeddingIndexerAgent:
    def __init__(self, directories, model_name="all-MiniLM-L6-v2"):
        self.directories = directories
        self.model = SentenceTransformer(model_name)
        self.index = []

    def run(self):
        print("🔍 Building embedding index...")
        for dir_path in self.directories:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(".java"):
                        full_path = os.path.join(root, file)
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = clean_markdown_code(f.read())
                        embedding = self.model.encode(content)
                        self.index.append({
                            "path": full_path,
                            "embedding": embedding.tolist()
                        })

        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(self.index, f)

        print(f"✅ Indexed {len(self.index)} files and saved to {INDEX_PATH}")