# agents/retry_agent.py

from agents.fix_and_compile import FixAndCompileAgent
from agents.build_validator import BuildValidatorAgent
from agents.build_fixer import BuildFixerAgent
from agents.gradle_dependency_validator import GradleDependencyValidatorAgent

class RetryAgent:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def retry_fix(self, target_path, fix_agent: FixAndCompileAgent, validator: BuildValidatorAgent,
                  context_stitcher, gradle_fixer: BuildFixerAgent,
                  dep_validator: GradleDependencyValidatorAgent = None, logger=None):
        attempt = 0
        fix_result = {}

        while attempt < self.max_retries:
            print(f"🔁 Retry attempt {attempt + 1} for {target_path}")
            fix_result = fix_agent.fix_file(target_path, context_stitcher)

            if validator.run_build():
                fix_result["success"] = True
                break

            build_log = validator.get_last_build_log()
            gradle_fixer.fix_gradle(build_log)

            if dep_validator:
                dep_validator.analyze_and_fix_conflicts()

            attempt += 1

        if not fix_result.get("success"):
            print(f"⚠️  Shim fallback: generating stub for {target_path}")
            shim_code = f"public class {target_path.split('/')[-1].replace('.java', '')} {{\n  // TODO: Shim generated due to unresolved errors.\n}}"
            fix_result["fixed_code"] = shim_code
            fix_result["fix_log"] = {"shim_generated": True}

        if logger:
            logger.log(target_path, fix_result)

        return fix_result
