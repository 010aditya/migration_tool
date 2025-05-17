# agents/retry_agent.py

import time
from agents.cross_reference_resolver import CrossReferenceResolverAgent

class RetryAgent:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def retry_fix(self, target_path, fix_agent, validator, context_stitcher, gradle_fixer, dep_validator, logger):
        attempt = 0
        success = False
        fix_result = None

        # Step 1: Run cross-reference resolver first
        print(f"🧩 Pre-pass: Resolving references for {target_path}")
        cross_resolver = CrossReferenceResolverAgent(fix_agent.output_dir)
        cross_resolver.resolve_and_patch(target_path)

        while attempt < self.max_retries and not success:
            print(f"🔁 Retry attempt {attempt + 1} for {target_path}")
            stitched_context = context_stitcher.stitch_context(target_path)
            fix_result = fix_agent.fix_file(target_path, stitched_context)

            if fix_result.get("success"):
                success = validator.run_build()
                if not success:
                    gradle_fixer.fix_gradle_file()
                    dep_validator.validate_dependencies()
            else:
                print(f"❌ Fix attempt {attempt + 1} failed for {target_path}")

            attempt += 1
            time.sleep(1)

        # Step 2: Post-pass resolver if still not successful
        if not success:
            print(f"🧩 Post-pass: Retrying reference resolution for {target_path}")
            cross_resolver.resolve_and_patch(target_path)
            success = validator.run_build()

        # Final fallback if still not fixed
        if not success:
            fix_result["shim_generated"] = True
            print(f"⚠️ Fallback shim will be used for {target_path}")

        fix_result["success"] = success
        logger.log_fix(target_path, fix_result)
        return fix_result