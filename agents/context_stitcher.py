# agents/context_stitcher.py

import os

class ContextStitcherAgent:
    def __init__(self, legacy_dir, migrated_dir, framework_dir=None, reference_promoter=None):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.framework_dir = framework_dir
        self.promoter = reference_promoter

    def stitch_context(self, target_path):
        parts = []

        # Read migrated code
        migrated_code = self._read_file(self.migrated_dir, target_path, label="Migrated")
        if migrated_code:
            parts.append(migrated_code)
        else:
            print(f"⚠️ Skipping {target_path} due to missing migrated content")

        # Read legacy code
        legacy_path = self._map_to_legacy_path(target_path)
        legacy_code = self._read_file(self.legacy_dir, legacy_path, label="Legacy")
        if legacy_code:
            parts.insert(0, legacy_code)

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
        # Conservative default: use same filename for legacy mapping
        return os.path.basename(target_path)

    def _try_read_framework_file(self, target_path):
        # Optional future support for scanning framework dirs
        return None
