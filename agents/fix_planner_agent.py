# fix_planner_agent.py

class FixPlannerAgent:
    def __init__(self, error_classifier, memory_manager):
        self.error_classifier = error_classifier
        self.memory = memory_manager

    def generate_plan(self, target_path, build_log, context):
        errors = self.error_classifier.classify(build_log)
        past_attempts = self.memory.get_attempts(target_path)

        fix_plan = []

        for err in errors:
            if err == "missing_import":
                if "resolve_imports" not in past_attempts:
                    fix_plan.append("resolve_imports")
            elif err == "unresolved_symbol":
                if "inject_missing_fields" not in past_attempts:
                    fix_plan.append("inject_missing_fields")
            elif err == "missing_method":
                if "suggest_method_stub" not in past_attempts:
                    fix_plan.append("suggest_method_stub")
            elif err == "package_mismatch":
                if "fix_package_declaration" not in past_attempts:
                    fix_plan.append("fix_package_declaration")

        if not fix_plan:
            # fallback for unknown or already tried errors
            fix_plan.append("llm_guided_fix")

        return {
            "plan": fix_plan,
            "reasoning": f"Based on {len(errors)} classified error(s) and memory history",
            "confidence": 0.75 + 0.05 * len(fix_plan)
        }

# Usage:
# planner = FixPlannerAgent(error_classifier, memory_manager)
# plan = planner.generate_plan(file_path, build_log, stitched_context)
