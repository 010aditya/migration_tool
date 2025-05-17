# agents/test_generator.py

import os
from llm.prompt_loader import load_prompt
from llm.markdown_utils import clean_markdown_code

TEST_PROMPT_PATH = "prompts/test_generation_prompt.txt"

class TestGeneratorAgent:
    def __init__(self, client, output_dir):
        self.client = client
        self.output_dir = output_dir
        self.test_output_dir = os.path.join(output_dir, "../test_cases")
        os.makedirs(self.test_output_dir, exist_ok=True)

    def generate_test_case(self, target_path):
        class_path = os.path.join(self.output_dir, target_path)
        if not os.path.exists(class_path):
            print(f"⚠️  Cannot generate test: file not found {class_path}")
            return

        with open(class_path, "r", encoding="utf-8") as f:
            code = f.read()

        prompt = load_prompt(TEST_PROMPT_PATH, {"code": code})
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        test_code = clean_markdown_code(response.choices[0].message.content)
        test_file_name = os.path.basename(target_path).replace(".java", "Test.java")
        test_file_path = os.path.join(self.test_output_dir, test_file_name)

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        print(f"✅ Generated test case: {test_file_path}")
