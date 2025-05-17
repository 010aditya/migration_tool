# agents/logger_refactor_agent.py

import os
import re
from llm.prompt_loader import load_prompt
from llm.markdown_utils import clean_markdown_code

PROMPT_PATH = "prompts/logger_refactor_prompt.txt"

class LoggerRefactorAgent:
    def __init__(self, client, output_dir):
        self.client = client
        self.output_dir = output_dir

    def inject_logger(self, file_path):
        full_path = os.path.join(self.output_dir, file_path)
        if not os.path.exists(full_path):
            print(f"⚠️  File not found for logger enhancement: {file_path}")
            return None

        with open(full_path, 'r', encoding='utf-8') as f:
            original_code = f.read()

        if not re.search(r'System\.out\.print|log\.', original_code):
            return None  # skip if no print/log statements found

        prompt = load_prompt(PROMPT_PATH, {"java_code": original_code})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            refactored_code = clean_markdown_code(response.choices[0].message.content)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(refactored_code)

            print(f"✅ Logging enhanced in: {file_path}")
            return refactored_code

        except Exception as e:
            print(f"❌ Failed to refactor logger in {file_path}: {e}")
            return None
