# fix_strategy_registry.py

from fix_strategies import resolve_imports, inject_missing_fields, fix_package_declaration
from llm_guided_fix_strategy import llm_guided_fix

class FixStrategy:
    def __init__(self, name, func, touches, safe=True):
        self.name = name
        self.func = func  # actual function to call
        self.touches = touches  # e.g., ["imports", "field_injection"]
        self.safe = safe

    def run(self, file_path, context, memory):
        return self.func(file_path=file_path, context=context, memory=memory)


class FixStrategyRegistry:
    def __init__(self):
        self.strategies = {}
        self._register_defaults()

    def register(self, name, func, touches=["general"], safe=True):
        self.strategies[name] = FixStrategy(name, func, touches, safe)

    def get_strategy(self, name):
        return self.strategies.get(name)

    def list_all(self):
        return list(self.strategies.keys())

    def execute(self, name, file_path, context, memory):
        strategy = self.get_strategy(name)
        if strategy:
            print(f"🔧 Executing strategy: {name} on {file_path}")
            return strategy.run(file_path, context, memory)
        else:
            print(f"❌ Strategy not found: {name}")
            return {"success": False, "reason": "strategy_not_found"}

    def _register_defaults(self):
        self.register("resolve_imports", resolve_imports, touches=["imports"], safe=True)
        self.register("inject_missing_fields", inject_missing_fields, touches=["field", "annotations"], safe=True)
        self.register("fix_package_declaration", fix_package_declaration, touches=["package"], safe=True)
        self.register("llm_guided_fix", llm_guided_fix, touches=["full_context"], safe=False)
