import os
import javalang
import json
import numpy as np
from src.utils.embedding_utils import get_embedder, cosine_similarity
# Import your wiring agent:
# from src.agents.internal_wiring_fixer_agent import InternalWiringFixerAgent

class RelationshipContextBuilderAgent:
    def __init__(self, legacy_dir, migrated_dir,
                 legacy_embedding_index_path, migrated_embedding_index_path,
                 output_path="data/relationship_context_report.json",
                 similarity_threshold=0.7,
                 trigger_missing_wires=False,  # Set to True to auto-trigger fixing
                 wiring_agent=None):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.output_path = output_path
        self.similarity_threshold = similarity_threshold
        self.embedder = get_embedder()
        self.trigger_missing_wires = trigger_missing_wires
        self.wiring_agent = wiring_agent

        # Load class-level embeddings for mapping
        with open(migrated_embedding_index_path, "r", encoding="utf-8") as f:
            self.migrated_embedding_index = json.load(f)
        with open(legacy_embedding_index_path, "r", encoding="utf-8") as f:
            self.legacy_embedding_index = json.load(f)

        self.migrated_classnames = {os.path.splitext(os.path.basename(fp))[0]: fp for fp in self.migrated_embedding_index}
        self.legacy_classnames = {os.path.splitext(os.path.basename(fp))[0]: fp for fp in self.legacy_embedding_index}

    def extract_class_relationships(self, root_dir, depth=2):
        # Returns: {class_name: set(related_class_names)}
        relationships = {}
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.java'):
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            code = f.read()
                        tree = javalang.parse.parse(code)
                        for node in tree.types:
                            if isinstance(node, javalang.tree.ClassDeclaration):
                                class_name = node.name
                                related = set()
                                # Field types
                                for field in node.fields:
                                    for decl in field.declarators:
                                        if field.type and hasattr(field.type, 'name'):
                                            related.add(field.type.name)
                                # Constructor params
                                for ctor in node.constructors:
                                    for p in ctor.parameters:
                                        if p.type and hasattr(p.type, 'name'):
                                            related.add(p.type.name)
                                # Method params/return types
                                for m in node.methods:
                                    if m.return_type and hasattr(m.return_type, 'name'):
                                        related.add(m.return_type.name)
                                    for p in m.parameters:
                                        if p.type and hasattr(p.type, 'name'):
                                            related.add(p.type.name)
                                    for path, inv in m.filter(javalang.tree.MethodInvocation):
                                        if inv.qualifier:
                                            related.add(inv.qualifier)
                                # Extends/implements
                                if node.extends:
                                    related.add(node.extends.name)
                                for impl in node.implements or []:
                                    related.add(impl.name)
                                # Transitive closure up to specified depth
                                if depth > 1:
                                    transitive_related = set(related)
                                    for _ in range(depth - 1):
                                        next_related = set()
                                        for rel in list(transitive_related):
                                            next_related |= relationships.get(rel, set())
                                        transitive_related |= next_related
                                    related = transitive_related
                                relationships[class_name] = related
                    except Exception as e:
                        print(f"[WARN] Could not parse {fpath}: {e}")
        return relationships

    def find_best_legacy_match(self, migrated_class):
        """Finds the best-matching legacy class for a given migrated class using embeddings."""
        if migrated_class in self.legacy_classnames:
            return migrated_class, 1.0
        if migrated_class not in self.migrated_classnames:
            return None, 0.0
        query_fp = self.migrated_classnames[migrated_class]
        query_vec = np.array(self.migrated_embedding_index[query_fp])
        best_score = -1.0
        best_legacy_class = None
        for legacy_class, legacy_fp in self.legacy_classnames.items():
            vec = np.array(self.legacy_embedding_index[legacy_fp])
            score = cosine_similarity(query_vec, vec)
            if score > best_score:
                best_score = score
                best_legacy_class = legacy_class
        return (best_legacy_class, best_score) if best_score > self.similarity_threshold else (None, best_score)

    def build_and_compare(self, depth=2):
        print("Extracting legacy relationships...")
        legacy_rel = self.extract_class_relationships(self.legacy_dir, depth=depth)
        print("Extracting migrated relationships...")
        migrated_rel = self.extract_class_relationships(self.migrated_dir, depth=depth)
        report = {}

        for m_class, m_related in migrated_rel.items():
            l_class, sim = self.find_best_legacy_match(m_class)
            if not l_class:
                continue
            l_related = legacy_rel.get(l_class, set())
            missing = sorted(list(l_related - m_related))
            extra = sorted(list(m_related - l_related))
            report[m_class] = {
                "legacy_class": l_class,
                "similarity": sim,
                "legacy_related": sorted(list(l_related)),
                "migrated_related": sorted(list(m_related)),
                "missing_in_migrated": missing,
                "extra_in_migrated": extra
            }
            # Optionally auto-trigger wiring agent
            if self.trigger_missing_wires and self.wiring_agent:
                for missing_class in missing:
                    print(f"[AUTO] Triggering wiring/port for missing class: {missing_class} in {m_class}")
                    self.wiring_agent.trigger_fix(m_class, missing_class)

        # Legacy classes not mapped at all
        for l_class in legacy_rel:
            found = any(l_class == report[mc]['legacy_class'] for mc in report)
            if not found:
                report[l_class] = {
                    "legacy_class": l_class,
                    "similarity": 1.0,
                    "legacy_related": sorted(list(legacy_rel[l_class])),
                    "migrated_related": [],
                    "missing_in_migrated": sorted(list(legacy_rel[l_class])),
                    "extra_in_migrated": []
                }

        # Save to JSON
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Relationship context report written to {self.output_path}")

# Example usage:
if __name__ == "__main__":
    # Optionally, pass a wiring_agent instance with .trigger_fix()
    agent = RelationshipContextBuilderAgent(
        legacy_dir="legacy_code/",
        migrated_dir="migrated_code/",
        legacy_embedding_index_path="data/legacy_embedding_index.json",
        migrated_embedding_index_path="data/embedding_index.json",
        output_path="data/relationship_context_report.json",
        similarity_threshold=0.7,
        trigger_missing_wires=False,   # Set True to trigger fixes
        wiring_agent=None              # Plug in your InternalWiringFixerAgent here!
    )
    agent.build_and_compare(depth=2)
