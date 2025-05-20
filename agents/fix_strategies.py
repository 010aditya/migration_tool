# fix_strategies.py

from agents.cross_reference_resolver import CrossReferenceResolverAgent
from agents.package_name_fixer import PackageNameFixerAgent
from agents.injection_fixer import InjectionFixerAgent

# Note: These strategies should be wired to your existing output_dir and agents as needed.

OUTPUT_DIR = "output/fixed_codebase"

# Strategy: Fix missing or incorrect imports
def resolve_imports(file_path, context, memory):
    try:
        resolver = CrossReferenceResolverAgent(migrated_dir=OUTPUT_DIR, class_index=context.get("class_index"))
        resolver.resolve(file_path)
        return {"success": True, "strategy": "resolve_imports"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Strategy: Inject missing fields based on usage (e.g., @Autowired services)
def inject_missing_fields(file_path, context, memory):
    try:
        fixer = InjectionFixerAgent(migrated_dir=OUTPUT_DIR, class_index=context.get("class_index"))
        fixer.fix(file_path)
        return {"success": True, "strategy": "inject_missing_fields"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Strategy: Fix incorrect or missing package declarations
def fix_package_declaration(file_path, context, memory):
    try:
        fixer = PackageNameFixerAgent(migrated_dir=OUTPUT_DIR)
        fixer.fix(file_path)
        return {"success": True, "strategy": "fix_package_declaration"}
    except Exception as e:
        return {"success": False, "error": str(e)}
