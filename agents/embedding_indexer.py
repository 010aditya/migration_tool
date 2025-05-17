# agents/embedding_indexer.py

import os
import json
from sentence_transformers import SentenceTransformer

class EmbeddingIndexerAgent:
    def __init__(self, source_dir, index_path="data/embedding_index.json"):
        self.source_dir = source_dir
        self.index_path = index_path
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def build_index(self):
        print(f"🔍 Indexing files from: {self.source_dir}")

        embedding_index = {}
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if file.endswith(".java"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.source_dir)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            embedding = self.model.encode(content, convert_to_tensor=False)
                            if embedding is not None and len(embedding) > 0:
                                embedding_index[rel_path] = {
                                    "content": content,
                                    "embedding": embedding
                                }
                            else:
                                print(f"⚠️ Skipped file with empty embedding: {rel_path}")
                    except Exception as e:
                        print(f"❌ Failed to embed {rel_path}: {e}")

        if not embedding_index:
            print("⚠️ No embeddings generated. Index will not be written.")
            return

        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(embedding_index, f, indent=2)
            print(f"✅ Embedding index written to {self.index_path}")