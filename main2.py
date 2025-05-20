# main.py

import os
import argparse
from agents.mapping_loader import MappingLoaderAgent
from agents.context_stitcher import ContextStitcherAgent
from agents.fix_and_compile import FixAndCompileAgent
from agents.build_validator import BuildValidatorAgent
from agents.build_fixer import BuildFixerAgent
from agents.retry_agent import RetryAgent
from agents.test_generator import TestGeneratorAgent
from agents.fix_history_logger import FixHistoryLogger
from agents.circular_dependency_detector import CircularDependencyDetectorAgent
from agents.swagger_completer_agent import SwaggerCompleterAgent
from agents.logger_refactor_agent import LoggerRefactorAgent
from agents.file_name_class_name_validator import FileNameClassNameValidatorAgent
from agents.relationship_builder_agent import RelationshipBuilderAgent
from llm.llm_client import get_llm_client

from smart_retry_agent import SmartRetryAgent
from agents.reference_promoter import ReferencePromoterAgent
from utils.project_structure import build_class_index

LEGACY_DIR = "legacy_codebase"
MIGRATED_DIR = "migrated_codebase"
OUTPUT_DIR = "output/fixed_codebase"
REFERENCE_DIR = "reference_pairs"
FRAMEWORK_DIR = "enterprise_framework_codebase"
MAPPING_PATH = "data/mapping.json"
BUILD_LOG_PATH = "logs/latest_build.log"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--migrate-all', action='store_true', help='Run full fix pipeline on all mapped files')
    args = parser.parse_args()

    print("🚀 Initializing agents...")
    FileNameClassNameValidatorAgent(MIGRATED_DIR).run()
    mapping_agent = MappingLoaderAgent(MAPPING_PATH)

    class_index = build_class_index(OUTPUT_DIR)
    promoter = ReferencePromoterAgent([REFERENCE_DIR])
    context_stitcher = ContextStitcherAgent(
        legacy_dir=LEGACY_DIR,
        migrated_dir=MIGRATED_DIR,
        framework_dir=FRAMEWORK_DIR,
        reference_promoter=promoter,
        mapping_agent=mapping_agent
    )

    smart_agent = SmartRetryAgent()

    if args.migrate_all:
        print("🧠 Starting Smart Retry Pipeline...")
        for target_file in mapping_agent.get_all_targets():
            print(f"\n🔧 Processing: {target_file}")
            stitched = context_stitcher.stitch_context(target_file)
            build_log = open(BUILD_LOG_PATH, encoding="utf-8").read() if os.path.exists(BUILD_LOG_PATH) else ""

            context = {
                "stitched": stitched,
                "build_log": build_log,
                "class_index": class_index
            }

            smart_agent.process(target_file, context, build_log)

        print("\n✅ All files processed. Running post-analysis...")
        cycle_detector = CircularDependencyDetectorAgent(OUTPUT_DIR)
        if cycle_detector.detect_cycles():
            print("❗Circular dependencies found. Review required.")
        else:
            print("✅ No circular dependencies detected.")

    print("\n✅ Done. Check logs/ and output/ for results.")


if __name__ == "__main__":
    import fire
    fire.Fire(main)
