import os
from agents.context_stitcher import ContextStitcherAgent
from agents.cross_reference_resolver import CrossReferenceResolverAgent
from agents.fix_and_compile import FixAndCompileAgent
from agents.build_validator import BuildValidatorAgent
from agents.gradle_dependency_validator import GradleDependencyValidatorAgent
from agents.build_fixer import BuildFixerAgent
from agents.fix_history_logger import FixHistoryLogger
from utils.build_log_filter import BuildLogFilter
from utils.project_structure_scanner import ProjectStructureScanner

class RetryAgent:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def retry_fix(self, target_file, fix_agent, validator, context_stitcher, gradle_fixer, dep_validator, logger):
        scanner = ProjectStructureScanner(fix_agent.output_dir)
        project_structure = scanner.collect_structure()

        for attempt in range(1, self.max_retries + 1):
            print(f"\n🔁 Attempt {attempt}/{self.max_retries} for: {target_file}")

            stitched_context = context_stitcher.stitch_context(target_file)
            build_log = validator.get_last_build_log()
            file_errors = BuildLogFilter.filter_log_for_file(build_log, target_file)

            # 🔍 Pre-fix wiring: run cross reference resolver first
            if attempt == 1:
                cross_resolver = CrossReferenceResolverAgent(fix_agent.output_dir, context_stitcher.promoter.class_index)
                cross_resolver.resolve(target_file)

            result = fix_agent.fix_file(target_file, stitched_context, file_errors)
            logger.log_fix_result(target_file, result)

            if result.get("success"):
                print(f"✅ Fix succeeded on attempt {attempt} for: {target_file}")
                return result

            # Optional post-fix: retry resolver again if final attempt fails
            if attempt == self.max_retries:
                print(f"🛠️ Final post-fix wiring check on: {target_file}")
                cross_resolver = CrossReferenceResolverAgent(fix_agent.output_dir, context_stitcher.promoter.class_index)
                cross_resolver.resolve(target_file)

                result = fix_agent.fix_file(target_file, stitched_context, file_errors)
                logger.log_fix_result(target_file, result)
                return result

        return {"success": False, "reason": "All fix attempts failed."}
