import json

def relationship_aware_fix_plan(
    mapping_json="data/mapping.json",
    relationship_json="data/legacy_relationships.json",
    build_log_path="data/build.log"
):
    # Load mappings and relationships
    legacy_to_migrated, migrated_to_legacy = load_mapping(mapping_json)
    with open(relationship_json, "r", encoding="utf-8") as f:
        legacy_relationships = json.load(f)
    broken_classes = parse_build_log(build_log_path)

    # For each broken migrated class
    for migrated_class in broken_classes:
        # Find legacy class (reverse mapping)
        legacy_class = None
        for mig, legs in migrated_to_legacy.items():
            if migrated_class == mig:
                legacy_class = legs[0]  # If multiple, you can enhance this
                break
        if not legacy_class:
            print(f"❌ Could not find legacy class for migrated class {migrated_class}")
            continue
        # Get related legacy classes
        related_legacy = legacy_relationships.get(legacy_class, [])
        # Map related legacy classes to migrated classes
        related_migrated = []
        for rel in related_legacy:
            migs = legacy_to_migrated.get(rel)
            if migs:
                related_migrated.extend(migs)
        print(f"\n=== Plan for broken migrated class: {migrated_class} ===")
        print(f"Legacy source: {legacy_class}")
        print(f"Related legacy classes: {related_legacy}")
        print(f"Mapped migrated equivalents: {related_migrated}")
        # (Here you would implement the logic to auto-wire, auto-import, or auto-stub based on these results)

        
if __name__ == "__main__":
    relationship_aware_fix_plan(
        mapping_json="data/mapping.json",
        relationship_json="data/legacy_relationships.json",
        build_log_path="data/build.log"
    )
