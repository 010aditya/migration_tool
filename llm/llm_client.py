# llm/llm_client.py

import os
from openai import OpenAI
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env if present

def get_llm_client():
    """
    Returns the correct LLM client instance based on environment variables.
    """
    provider = os.getenv("LLM_PROVIDER", "azure").lower()

    if provider == "openai":
        return OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            organization=os.getenv("OPENAI_ORG")  # Optional
        )
    elif provider == "azure":
        return AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-07-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
