# llm/prompt_loader.py

import os


def load_prompt(path, replacements=None):
    """
    Load a prompt from file and substitute placeholders with replacements.
    :param path: Path to the prompt template file.
    :param replacements: Dict of placeholders and their values.
    :return: Final prompt string.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        prompt = f.read()

    if replacements:
        for key, value in replacements.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", value)

    return prompt
