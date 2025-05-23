# src/utils/embedding_utils.py

import os
import numpy as np
from langchain_openai import AzureOpenAIEmbeddings

def get_embedder():
    return AzureOpenAIEmbeddings(
        azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        openai_api_version=os.environ["OPENAI_API_VERSION"],
        openai_api_key=os.environ["OPENAI_API_KEY"],
        openai_api_base=os.environ["OPENAI_API_BASE"],
        openai_api_type="azure"
    )

def embed_code_file(file_path, embedder):
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    # Returns a 1D numpy array (embedding vector)
    return np.array(embedder.embed_documents([code])[0])

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
