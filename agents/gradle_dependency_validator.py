# agents/gradle_dependency_validator.py

import os
import subprocess
from llm.prompt_loader import load_prompt
from llm.markdown_utils import clean_markdown_code

PROMPT_PATH = "prompts/gradle_dependency_tree_prompt.txt"

class GradleDependencyValidatorAgent:
    def __init__(self, client, project_dir):
        self.client = client
        self.project_dir = project_dir

    def analyze_and_fix_conflicts(self):
        print("🔍 Running Gradle dependency insight...")

        try:
            result = subprocess.run(
                ["./gradlew", "dependencies", "--configuration", "runtimeClasspath"],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            dep_tree = result.stdout

            if "FAILED" in dep_tree or result.returncode != 0:
                print("⚠️  Failed to fetch dependency tree")
                return False

            prompt = load_prompt(PROMPT_PATH, {"dependency_tree": dep_tree})

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            updated_gradle = clean_markdown_code(response.choices[0].message.content)
            gradle_file = os.path.join(self.project_dir, "build.gradle")

            with open(gradle_file, "w", encoding="utf-8") as f:
                f.write(updated_gradle)

            print("✅ build.gradle updated to resolve dependency conflicts.")
            return True

        except Exception as e:
            print(f"❌ Exception in GradleDependencyValidatorAgent: {e}")
            return False
