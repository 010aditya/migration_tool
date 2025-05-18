# agents/context_stitcher.py

import os
import json

class ContextStitcherAgent:
    def __init__(self, legacy_dir, migrated_dir, framework_dir=None, reference_promoter=None, mapping_agent=None):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.framework_dir = framework_dir
        self.promoter = reference_promoter
        self.mapping_agent = mapping_agent
        self.relationship_dir = os.path.join(migrated_dir, "../relationships")

    def stitch_context(self, target_path):
        parts = []

        # Load relationship file if available
        relationship = self._load_relationship(target_path)

        # Add legacy code
        legacy_paths = relationship.get("legacySources", []) if relationship else [self._map_to_legacy_path(target_path)]
        for legacy_path in legacy_paths:
            legacy_code = self._read_file(self.legacy_dir, legacy_path, label="Legacy")
            if legacy_code:
                parts.append(legacy_code)

        # Add target file
        migrated_code = self._read_file(self.migrated_dir, target_path, label="Migrated")
        if migrated_code:
            parts.append(migrated_code)
        else:
            print(f"⚠️ Skipping {target_path} due to missing migrated content")

        # Add related co-migrated files
        if relationship:
            for related in relationship.get("relatedMigratedTargets", []):
                related_code = self._read_file(self.migrated_dir, related, label="Related Target")
                if related_code:
                    parts.append(related_code)

        # Optionally add framework context
        if self.framework_dir:
            framework_code = self._try_read_framework_file(target_path)
            if framework_code:
                parts.append(framework_code)

        # Add reference files if promoter is present and valid
        if self.promoter:
            try:
                similar_refs = self.promoter.get_similar_files(migrated_code or "")
                for ref_path in similar_refs:
                    ref_code = self._read_file("reference_pairs/migrated", ref_path, label="Reference")
                    if ref_code:
                        parts.append(ref_code)
            except Exception as e:
                print(f"⚠️ Reference promoter failed: {e}")

        return "\n\n".join(p for p in parts if p)

    def _read_file(self, base_dir, relative_path, label=""):
        full_path = os.path.join(base_dir, relative_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    return f"// --- {label} File: {relative_path} ---\n" + f.read()
            except Exception as e:
                print(f"❌ Error reading {label} file {relative_path}: {e}")
                return ""
        else:
            print(f"⚠️ {label} file not found: {full_path}")
            return ""

    def _map_to_legacy_path(self, target_path):
        if self.mapping_agent:
            return self.mapping_agent.get_source_for_target(target_path) or os.path.basename(target_path)
        return os.path.basename(target_path)

    def _try_read_framework_file(self, target_path):
        return None

    def _load_relationship(self, target_path):
        filename = os.path.basename(target_path).replace(".java", "") + "_relationship.json"
        rel_path = os.path.join(self.relationship_dir, filename)
        if os.path.exists(rel_path):
            try:
                with open(rel_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error loading relationship for {target_path}: {e}")
        return None
