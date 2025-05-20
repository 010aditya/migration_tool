 # smart_retry_agent.py

from fix_strategy_registry import FixStrategyRegistry
from fix_planner_agent import FixPlannerAgent
from fix_memory_manager import FixMemoryManager
from error_classifier import ErrorClassifier

class SmartRetryAgent:
    def __init__(self):
        self.registry = FixStrategyRegistry()
        self.memory = FixMemoryManager()
        self.classifier = ErrorClassifier()
        self.planner = FixPlannerAgent(self.classifier, self.memory)

    def process(self, target_file, context, build_log):
        plan = self.planner.generate_plan(target_file, build_log, context)
        print(f"🧠 Fix plan for {target_file}: {plan['plan']} (confidence={plan['confidence']})")

        for strategy_name in plan["plan"]:
            result = self.registry.execute(strategy_name, target_file, context, self.memory)
            self.memory.record_attempt(target_file, strategy_name)

            if result.get("success"):
                print(f"✅ Strategy {strategy_name} succeeded for {target_file}")
                return result  # Stop on first success
            else:
                print(f"❌ Strategy {strategy_name} failed for {target_file}")

        print(f"🛑 All strategies exhausted for {target_file} without success.")
        return {"success": False, "reason": "all_strategies_failed"}
