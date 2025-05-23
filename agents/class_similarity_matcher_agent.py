import os
import json
import numpy as np
from src.utils.embedding_utils import get_embedder, embed_code_file, cosine_similarity

class ClassSimilarityMatcherAgent:
    def __init__(self, embedding_index_path, logger=None, similarity_threshold=0.7):
        """
        :param embedding_index_path: Path to the JSON file of precomputed migrated code embeddings
        :param logger: Callable for logging (optional)
        :param similarity_threshold: Minimum similarity score to accept a match
        """
        self.embedding_index_path = embedding_index_path
        self.similarity_threshold = similarity_threshold
        self.logger = logger or self.default_logger
        self.embedder = get_embedder()

        with open(self.embedding_index_path, "r", encoding="utf-8") as f:
            self.embedding_index = json.load(f)

    def default_logger(self, event):
        print(event)

    def find_best_match(self, query_class_path):
        """
        Given a class file (legacy or missing in migrated), find the closest match in migrated code.
        Returns: (best_match_path, best_score) if above threshold, else (None, None)
        """
        if not os.path.exists(query_class_path):
            self.logger({"type": "file_not_found", "file": query_class_path})
            return None, None

        try:
            query_vec = embed_code_file(query_class_path, self.embedder)
        except Exception as e:
            self.logger({"type": "embedding_error", "file": query_class_path, "error": str(e)})
            return None, None

        best_score = -1.0
        best_file = None
        for file_path, vec in self.embedding_index.items():
            score = cosine_similarity(query_vec, np.array(vec))
            if score > best_score:
                best_score = score
                best_file = file_path

        if best_score >= self.similarity_threshold:
            self.logger({
                "type": "similarity_match",
                "query_class": query_class_path,
                "matched_class": best_file,
                "similarity_score": best_score
            })
            return best_file, best_score
        else:
            self.logger({
                "type": "no_suitable_match",
                "query_class": query_class_path,
                "best_candidate": best_file,
                "best_score": best_score,
                "note": "Below similarity threshold"
            })
            return None, None

# Example usage (for direct testing):
if __name__ == "__main__":
    matcher = ClassSimilarityMatcherAgent(
        embedding_index_path="data/embedding_index.json",
        similarity_threshold=0.7
    )
    best_file, score = matcher.find_best_match("legacy_code/com/example/CustomerBean.java")
    if best_file:
        print(f"Best match: {best_file} (similarity={score:.3f})")
    else:
        print("No sufficiently similar match found.")
