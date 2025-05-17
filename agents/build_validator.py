# agents/build_validator.py

import subprocess
import os

class BuildValidatorAgent:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.log_path = "logs/build_logs/latest_build.log"

    def run_build(self):
        print("🛠️  Running gradle clean build...")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as log_file:
            result = subprocess.run(
                ["./gradlew", "clean", "build"],
                cwd=self.project_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT
            )

        build_success = result.returncode == 0
        if build_success:
            print("✅ Gradle build successful")
        else:
            print("❌ Gradle build failed. See logs/build_logs/latest_build.log")
        return build_success

    def get_last_build_log(self):
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""