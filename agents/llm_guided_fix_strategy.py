# llm_guided_fix_strategy.py

from llm.llm_client import get_llm_client
from utils.clean_markdown_code import clean_markdown_code
from agents.fix_and_compile import FixAndCompileAgent

LEGACY_DIR = "legacy_codebase"
MIGRATED_DIR = "migrated_codebase"
OUTPUT_DIR = "output/fixed_codebase"

# LLM-guided fallback strategy
def llm_guided_fix(file_path, context, memory):
    try:
        client = get_llm_client()
        fix_agent = FixAndCompileAgent(client, LEGACY_DIR, MIGRATED_DIR, OUTPUT_DIR)

        stitched_context = context.get("stitched") or ""
        build_log = context.get("build_log") or ""

        result = fix_agent.fix_file(
            target_path=file_path,
            stitched_context=stitched_context,
            build_log=build_log
        )

        return {
            "success": result.get("success", False),
            "strategy": "llm_guided_fix",
            "llm_delta": result.get("fix_log", {})
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
