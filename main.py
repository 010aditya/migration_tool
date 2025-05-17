# main.py

import os
import argparse
from agents.file_name_class_name_validator import FileNameClassNameValidatorAgent
from agents.mapping_loader import MappingLoaderAgent
from agents.context_stitcher import ContextStitcherAgent
from agents.fix_and_compile import FixAndCompileAgent
from agents.build_validator import BuildValidatorAgent
from agents.build_fixer import BuildFixerAgent
from agents.gradle_dependency_validator import GradleDependencyValidatorAgent
from agents.retry_agent import RetryAgent
from agents.test_generator import TestGeneratorAgent
from agents.fix_history_logger import FixHistoryLogger
from agents.circular_dependency_detector import CircularDependencyDetectorAgent
from agents.swagger_completer_agent import SwaggerCompleterAgent
from agents.logger_refactor_agent import LoggerRefactorAgent
from llm.llm_client import get_llm_client

LEGACY_DIR = "legacy_codebase"
MIGRATED_DIR = "migrated_codebase"
OUTPUT_DIR = "output/fixed_codebase"
REFERENCE_DIR = "reference_pairs"
FRAMEWORK_DIR = "enterprise_framework_codebase"
MAPPING_PATH = "data/mapping.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--migrate-all', action='store_true', help='Run full fix pipeline on all mapped files')
    args = parser.parse_args()

    print("🚀 Initializing agents...")
    FileNameClassNameValidatorAgent(MIGRATED_DIR).run()

    mapping_agent = MappingLoaderAgent(MAPPING_PATH)
    client = get_llm_client()

    context_stitcher = ContextStitcherAgent(
        migrated_dir=MIGRATED_DIR,
        reference_dir=REFERENCE_DIR,
        framework_dir=FRAMEWORK_DIR,
        mapping_agent=mapping_agent
    )
    fix_agent = FixAndCompileAgent(client, LEGACY_DIR, MIGRATED_DIR, OUTPUT_DIR)
    validator = BuildValidatorAgent(OUTPUT_DIR)
    fixer = BuildFixerAgent(client, OUTPUT_DIR)
    dep_validator = GradleDependencyValidatorAgent(client, OUTPUT_DIR)
    retry_agent = RetryAgent(max_retries=3)
    tester = TestGeneratorAgent(client, OUTPUT_DIR)
    swagger_agent = SwaggerCompleterAgent(client, OUTPUT_DIR)
    logger_agent = LoggerRefactorAgent(client, OUTPUT_DIR)
    logger = FixHistoryLogger()

    if args.migrate_all:
        print("🧠 Starting full migration fix pipeline...")
        for target_file in mapping_agent.get_all_targets():
            print(f"\n🔧 Processing: {target_file}")
            result = retry_agent.retry_fix(
                target_file,
                fix_agent=fix_agent,
                validator=validator,
                context_stitcher=context_stitcher,
                gradle_fixer=fixer,
                dep_validator=dep_validator,
                logger=logger
            )
            if result.get("success"):
                tester.generate_test_case(target_file)
                swagger_agent.add_swagger_annotations(target_file)
                logger_agent.inject_logger(target_file)

        print("\n✅ All files processed.")
        print("🔍 Scanning for circular dependencies...")
        cycle_detector = CircularDependencyDetectorAgent(OUTPUT_DIR)
        cycles = cycle_detector.detect_cycles()
        if cycles:
            print("❗Circular dependencies found. Review required.")
        else:
            print("✅ No circular dependencies detected.")

    print("\n✅ Done. Check logs/ and output/ for results.")


if __name__ == "__main__":
    import fire
   fire.Fire(main)
