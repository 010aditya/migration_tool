import os
import json
from src.utils.embedding_utils import get_embedder, embed_code_file

def scan_java_files(directory):
    java_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    return java_files

def build_embedding_index(directory, output_path):
    embedder = get_embedder()
    java_files = scan_java_files(directory)
    index = {}
    print(f"Found {len(java_files)} Java files in {directory}. Embedding...")
    for i, file_path in enumerate(java_files):
        try:
            emb = embed_code_file(file_path, embedder)
            index[file_path] = emb
            print(f"[{i+1}/{len(java_files)}] Embedded {file_path}")
        except Exception as e:
            print(f"Error embedding {file_path}: {e}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f)
    print(f"✅ Embedding index written to {output_path}")

if __name__ == "__main__":
    # Example usage: python embedding_indexer.py migrated_code/ data/embedding_index.json
    import sys
    if len(sys.argv) != 3:
        print("Usage: python embedding_indexer.py <java_directory> <output_index.json>")
        exit(1)
    build_embedding_index(sys.argv[1], sys.argv[2])
