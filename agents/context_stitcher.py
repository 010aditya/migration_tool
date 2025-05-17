# agents/context_stitcher.py

import os
from agents.mapping_loader import MappingLoaderAgent
from agents.reference_promoter import ReferencePromoterAgent

class ContextStitcherAgent:
    def __init__(self, migrated_dir, reference_dir, framework_dir, mapping_agent):
        self.migrated_dir = migrated_dir
        self.reference_dir = reference_dir
        self.framework_dir = framework_dir
        self.mapping_agent = mapping_agent
        self.promoter = ReferencePromoterAgent([reference_dir, framework_dir])

    def stitch_context(self, target_file):
        stitched_parts = []

        # 1. Primary file
        target_path = os.path.join(self.migrated_dir, target_file)
        stitched_parts.append(self._read_file("PRIMARY FILE", target_path))

        # 2. Related targets from mapping
        sources = self.mapping_agent.get_sources_by_target(target_file)
        for src in sources:
            for related in self.mapping_agent.get_targets_by_source(src):
                full_path = os.path.join(self.migrated_dir, related)
                if related != target_file and os.path.exists(full_path):
                    stitched_parts.append(self._read_file("RELATED FILE", full_path))

        # 3. Similar reference files
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
        similar_refs = self.promoter.get_similar_files(content, top_k=5)
        for ref_path in similar_refs:
            if os.path.exists(ref_path):
                stitched_parts.append(self._read_file("REFERENCE FILE", ref_path))

        return "\n\n".join(stitched_parts)

    def _read_file(self, tag, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            return f"// === {tag}: {os.path.basename(path)} ===\n{code}"
        except Exception as e:
            return f"// === {tag} LOAD ERROR: {path} ===\n// {e}"
