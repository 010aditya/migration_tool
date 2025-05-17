# agents/swagger_completer_agent.py

import os
import re
from llm.prompt_loader import load_prompt
from llm.markdown_utils import clean_markdown_code

PROMPT_PATH = "prompts/swagger_completion_prompt.txt"

class SwaggerCompleterAgent:
    def __init__(self, client, output_dir):
        self.client = client
        self.output_dir = output_dir

    def add_swagger_annotations(self, file_path):
        full_path = os.path.join(self.output_dir, file_path)
        if not os.path.exists(full_path):
            print(f"⚠️  File not found for Swagger update: {file_path}")
            return None

        with open(full_path, 'r', encoding='utf-8') as f:
            original_code = f.read()

        if not re.search(r'@RestController|@Controller', original_code):
            return None  # skip non-controller files

        prompt = load_prompt(PROMPT_PATH, {"java_code": original_code})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            annotated_code = clean_markdown_code(response.choices[0].message.content)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(annotated_code)

            print(f"✅ Swagger annotations added to: {file_path}")
            return annotated_code

        except Exception as e:
            print(f"❌ Failed to annotate Swagger for {file_path}: {e}")
            return None
