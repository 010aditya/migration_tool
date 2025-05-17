# tests/test_pipeline.py

import os
import shutil
import subprocess
from agents.file_name_class_name_validator import FileNameClassNameValidatorAgent
from agents.mapping_loader import MappingLoaderAgent
from agents.context_stitcher import ContextStitcherAgent
from agents.fix_and_compile import FixAndCompileAgent
from agents.build_validator import BuildValidatorAgent
from agents.build_fixer import BuildFixerAgent
from agents.retry_agent import RetryAgent
from agents.test_generator import TestGeneratorAgent
from agents.fix_history_logger import FixHistoryLogger
from llm.llm_client import get_llm_client

LEGACY_DIR = "legacy_codebase"
MIGRATED_DIR = "migrated_codebase"
OUTPUT_DIR = "output/fixed_codebase"
REFERENCE_DIR = "reference_pairs"
FRAMEWORK_DIR = "enterprise_framework_codebase"
MAPPING_PATH = "data/mapping.json"

# Test entry point
if __name__ == "__main__":
    print("🧪 Running Migration Assist Test Pipeline")

    # Clean output folder
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    FileNameClassNameValidatorAgent(MIGRATED_DIR).run()
    mapping_agent = MappingLoaderAgent(MAPPING_PATH)
    context_stitcher = ContextStitcherAgent(MIGRATED_DIR, REFERENCE_DIR, FRAMEWORK_DIR, mapping_agent)
    fix_logger = FixHistoryLogger()

    client = get_llm_client()
    fix_agent = FixAndCompileAgent(client, LEGACY_DIR, MIGRATED_DIR, OUTPUT_DIR)
    validator = BuildValidatorAgent(OUTPUT_DIR)
    fixer = BuildFixerAgent(client, OUTPUT_DIR)
    retry_agent = RetryAgent(max_retries=3)
    tester = TestGeneratorAgent(client, OUTPUT_DIR)

    # Run test on each file from mapping
    for target_file in mapping_agent.get_all_targets():
        print(f"\n🔧 Testing fix for: {target_file}")
        result = retry_agent.retry_fix(
            target_file,
            fix_agent=fix_agent,
            validator=validator,
            context_stitcher=context_stitcher,
            gradle_fixer=fixer,
            logger=fix_logger
        )

        if result.get("success"):
            tester.generate_test_case(target_file)
        else:
            print(f"⚠️  Final fallback (shim) used for: {target_file}")

    print("\n🧪 Running './gradlew test' to validate generated tests...")
    try:
        result = subprocess.run([
            "./gradlew", "test"
        ], cwd=OUTPUT_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        test_log = result.stdout
        print("\n--- Test Execution Output ---")
        print(test_log)

        if "BUILD SUCCESSFUL" in test_log:
            print("✅ All tests passed.")
        else:
            print("❌ Some tests failed. Check output above.")

    except Exception as e:
        print(f"❌ Failed to execute tests: {e}")

    print("\n✅ Test pipeline completed. Check logs/ and output/")