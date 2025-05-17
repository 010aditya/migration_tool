# agents/reference_promoter.py

import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

INDEX_PATH = "data/embedding_index.json"

class ReferencePromoterAgent:
    def __init__(self, reference_dirs, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.reference_dirs = reference_dirs
        self.index = self._load_index()

    def _load_index(self):
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(f"Embedding index not found: {INDEX_PATH}")
        with open(INDEX_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_similar_files(self, input_code, top_k=5):
        input_embedding = self.model.encode(input_code)
        index_embeddings = np.array([entry["embedding"] for entry in self.index])

        similarities = cosine_similarity([input_embedding], index_embeddings)[0]
        ranked = sorted(zip(similarities, self.index), key=lambda x: -x[0])
        return [entry["path"] for _, entry in ranked[:top_k]]