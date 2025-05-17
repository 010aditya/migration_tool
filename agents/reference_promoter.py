# agents/reference_promoter.py

import os
import json
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity

INDEX_PATH = "data/embedding_index.json"

class ReferencePromoterAgent:
    def __init__(self, reference_dirs, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.reference_dirs = reference_dirs
        self.embedding_index = self._load_index()  # ✅ Assign the loaded index

    def _load_index(self):
        if not os.path.exists(INDEX_PATH):
            print(f"ℹ️  Index file not found at {INDEX_PATH}, proceeding without reference.")
            return {}
        try:
            with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load embedding index: {e}")
            return {}

    def get_similar_files(self, input_code, top_k=5):
        if not self.embedding_index:
            print("⚠️ No embedding index found or it's empty. Skipping similarity check.")
            return []

        input_embedding = self.model.encode(input_code, convert_to_tensor=False)

        index_embeddings = []
        file_refs = []

        for file_path, data in self.embedding_index.items():
            embedding = data.get("embedding")
            if embedding:
                index_embeddings.append(embedding)
                file_refs.append(file_path)

        if not index_embeddings:
            print("⚠️ No valid reference embeddings found in the index. Skipping reference promotion.")
            return []

        try:
            similarities = cosine_similarity([input_embedding], index_embeddings)[0]
        except Exception as e:
            print(f"❌ Failed to compute cosine similarity: {e}")
            return []

        scored = sorted(zip(file_refs, similarities), key=lambda x: x[1], reverse=True)
        return [path for path, score in scored[:top_k]]
