# agents/build_fixer.py

import os
from llm.prompt_loader import load_prompt
from llm.markdown_utils import clean_markdown_code

GRADLE_PATH = "build.gradle"
PROMPT_PATH = "prompts/gradle_fix_prompt.txt"

class BuildFixerAgent:
    def __init__(self, client, output_dir):
        self.client = client
        self.output_dir = output_dir

    def fix_gradle(self, build_log):
        gradle_file = os.path.join(self.output_dir, GRADLE_PATH)
        if not os.path.exists(gradle_file):
            print("⚠️  build.gradle not found, creating default...")
            open(gradle_file, 'w', encoding='utf-8').write("plugins { id 'java' }")

        with open(gradle_file, 'r', encoding='utf-8') as f:
            gradle_content = f.read()

        prompt = load_prompt(PROMPT_PATH, {
            "gradle": gradle_content,
            "errors": build_log
        })

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        fixed_gradle = clean_markdown_code(response.choices[0].message.content)

        with open(gradle_file, 'w', encoding='utf-8') as f:
            f.write(fixed_gradle)

        print("🛠️  Updated build.gradle based on build log errors.")
