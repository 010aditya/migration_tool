# agents/fix_and_compile.py

import os
from llm.prompt_loader import load_prompt
from llm.markdown_utils import clean_markdown_code

PROMPT_PATH = "prompts/fix_and_compile_prompt.txt"

class FixAndCompileAgent:
    def __init__(self, client, legacy_dir, migrated_dir, output_dir):
        self.client = client
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.output_dir = output_dir

    def fix_file(self, target_path, stitcher):
        assert self.legacy_dir not in target_path, "❌ Attempted to write to legacy directory. Aborting."

        migrated_file_path = os.path.join(self.migrated_dir, target_path)
        if not os.path.exists(migrated_file_path):
            print(f"❌ File not found: {migrated_file_path}")
            return {"fix_log": {"file_missing": True}, "fixed_code": ""}

        with open(migrated_file_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        # stitch context
        context = stitcher.stitch_context(target_path)
        prompt = load_prompt(PROMPT_PATH, {
            "broken_code": original_code,
            "references": context
        })

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        fixed_code = clean_markdown_code(response.choices[0].message.content)
        output_path = os.path.join(self.output_dir, target_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)

        return {
            "fix_log": {"fixed": True},
            "fixed_code": fixed_code
        }
