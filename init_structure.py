import os

BASE_DIR = "migration_assist"

# Folder structure to create
folders = [
    "agents",
    "llm",
    "scripts",
    "data",
    "logs/fix_history",
    "logs/build_logs",
    "output/fixed_codebase",
    "output/test_cases",
    "reference_pairs",
    "legacy_codebase",
    "migrated_codebase",
    "enterprise_framework_codebase",
    "prompts",
    "config"
]

# Placeholder agent files
agent_files = {
    "agents": [
        "file_name_class_name_validator.py",
        "mapping_loader.py",
        "embedding_indexer.py",
        "reference_promoter.py",
        "context_stitcher.py",
        "fix_and_compile.py",
        "build_validator.py",
        "build_fixer.py",
        "retry_agent.py",
        "test_generator.py",
        "fix_history_logger.py",
        "jsp_thymeleaf_resolver.py"  # Optional agent
    ],
    "llm": [
        "llm_client.py",
        "prompt_loader.py",
        "markdown_utils.py"
    ],
    "scripts": [
        "run_all_agents.py",
        "init.sh",
        "init.bat"
    ],
    "prompts": [
        "fix_and_compile_prompt.txt",
        "gradle_fix_prompt.txt",
        "reference_extraction_prompt.txt"
    ],
    "config": [
        "settings.yaml",
        "azure_llm_config.json"
    ]
}

# Create directories
for folder in folders:
    path = os.path.join(BASE_DIR, folder)
    os.makedirs(path, exist_ok=True)

# Create placeholder files
for subfolder, files in agent_files.items():
    for file in files:
        file_path = os.path.join(BASE_DIR, subfolder, file)
        with open(file_path, "w", encoding="utf-8") as f:
            if file.endswith(".py"):
                f.write(f"# {file.replace('_', ' ').title()} Placeholder\n\n")
            elif file.endswith(".txt"):
                f.write(f"# Prompt: {file}\n\n")
            elif file.endswith(".sh") or file.endswith(".bat"):
                f.write(f"# {file} script\n")
            elif file.endswith(".yaml") or file.endswith(".json"):
                f.write("{}\n")

print(f"✅ Project structure created under ./{BASE_DIR}")
