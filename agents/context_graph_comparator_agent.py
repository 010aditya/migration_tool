import os
import javalang
import json
import numpy as np
from src.utils.embedding_utils import get_embedder, cosine_similarity

class ContextGraphComparatorAgent:
    def __init__(self, 
                 legacy_dir, 
                 migrated_dir, 
                 reference_projects=None, 
                 legacy_embedding_index_path=None, 
                 migrated_embedding_index_path=None, 
                 output_path="data/context_graph_comparison.json", 
                 similarity_threshold=0.7, 
                 neighborhood_depth=1):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.reference_projects = reference_projects or []  # [{legacy_dir, migrated_dir, legacy_embedding_index, migrated_embedding_index}]
        self.legacy_embedding_index_path = legacy_embedding_index_path
        self.migrated_embedding_index_path = migrated_embedding_index_path
        self.output_path = output_path
        self.similarity_threshold = similarity_threshold
        self.neighborhood_depth = neighborhood_depth
        self.embedder = get_embedder()
        self.legacy_embeddings = self._load_embeddings(legacy_embedding_index_path)
        self.migrated_embeddings = self._load_embeddings(migrated_embedding_index_path)

    def _load_embeddings(self, index_path):
        if index_path and os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def build_class_graph(self, root_dir):
        # Returns: {class_name: {"calls": set(...), "called_by": set(...)}}
        class_graph = {}
        file_class_map = {}  # {filename: [class_names]}
        class_files = {}     # {class_name: filename}
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
                                cname = node.name
                                file_class_map.setdefault(fpath, []).append(cname)
                                class_files[cname] = fpath
                                calls = set()
                                # Field types and param types
                                for field in node.fields:
                                    if field.type and hasattr(field.type, 'name'):
                                        calls.add(field.type.name)
                                for ctor in node.constructors:
                                    for p in ctor.parameters:
                                        if p.type and hasattr(p.type, 'name'):
                                            calls.add(p.type.name)
                                # Methods: param types, return types, call targets
                                for m in node.methods:
                                    if m.return_type and hasattr(m.return_type, 'name'):
                                        calls.add(m.return_type.name)
                                    for p in m.parameters:
                                        if p.type and hasattr(p.type, 'name'):
                                            calls.add(p.type.name)
                                    # Method invocations
                                    for path, inv in m.filter(javalang.tree.MethodInvocation):
                                        if inv.qualifier:
                                            calls.add(inv.qualifier)
                                # Extends/Implements
                                if node.extends:
                                    calls.add(node.extends.name)
                                for impl in node.implements or []:
                                    calls.add(impl.name)
                                class_graph[cname] = {"calls": calls, "called_by": set()}
                    except Exception as e:
                        print(f"[WARN] Could not parse {fpath}: {e}")
        # Fill in 'called_by'
        for caller, v in class_graph.items():
            for callee in v["calls"]:
                if callee in class_graph:
                    class_graph[callee]["called_by"].add(caller)
        return class_graph

    def get_neighborhood(self, class_graph, class_name, depth=1):
        visited = set()
        to_visit = {class_name}
        neighborhood = set()
        for _ in range(depth):
            next_visit = set()
            for c in to_visit:
                if c in class_graph and c not in visited:
                    neighborhood |= class_graph[c]["calls"]
                    neighborhood |= class_graph[c]["called_by"]
                    next_visit |= class_graph[c]["calls"]
                    next_visit |= class_graph[c]["called_by"]
                    visited.add(c)
            to_visit = next_visit - visited
        return neighborhood

    def compare_graphs(self):
        print("Building legacy class graph...")
        legacy_graph = self.build_class_graph(self.legacy_dir)
        print("Building migrated class graph...")
        migrated_graph = self.build_class_graph(self.migrated_dir)
        report = {}

        for m_class in migrated_graph:
            # 1. Find best matching legacy class (embedding or by name)
            l_class, sim = self.find_best_legacy_match(m_class)
            if not l_class:
                continue
            # 2. Extract neighborhoods
            l_neigh = self.get_neighborhood(legacy_graph, l_class, depth=self.neighborhood_depth)
            m_neigh = self.get_neighborhood(migrated_graph, m_class, depth=self.neighborhood_depth)
            # 3. Node-wise similarity (embeddings) and set diff
            missing = [x for x in l_neigh if x not in m_neigh]
            extra = [x for x in m_neigh if x not in l_neigh]
            # 4. Optionally, consult reference projects for guidance
            guidance = None
            if self.reference_projects:
                guidance = self.find_reference_guidance(l_class, m_class)
            report[m_class] = {
                "legacy_class": l_class,
                "similarity": sim,
                "legacy_neighborhood": sorted(list(l_neigh)),
                "migrated_neighborhood": sorted(list(m_neigh)),
                "missing_in_migrated": sorted(missing),
                "extra_in_migrated": sorted(extra),
                "reference_guidance": guidance
            }
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Context graph comparison report written to {self.output_path}")

    def find_best_legacy_match(self, migrated_class):
        # Prefer name match
        if migrated_class in self.legacy_embeddings:
            return migrated_class, 1.0
        if not self.migrated_embeddings or not self.legacy_embeddings:
            return None, 0.0
        m_vec = np.array(self.migrated_embeddings.get(migrated_class, []))
        if not m_vec.any():
            return None, 0.0
        best_score = -1.0
        best_class = None
        for legacy_class, vec in self.legacy_embeddings.items():
            score = cosine_similarity(m_vec, np.array(vec))
            if score > best_score:
                best_score = score
                best_class = legacy_class
        return (best_class, best_score) if best_score > self.similarity_threshold else (None, best_score)

    def find_reference_guidance(self, l_class, m_class):
        # For each reference project, find the best matching legacy class/subgraph
        best_sim = 0.0
        best_pair = None
        for ref in self.reference_projects:
            legacy_emb = ref.get('legacy_embedding_index')
            migrated_emb = ref.get('migrated_embedding_index')
            if not legacy_emb or not migrated_emb:
                continue
            l_vec = np.array(self.legacy_embeddings.get(l_class, []))
            for ref_lc, ref_vec in legacy_emb.items():
                sim = cosine_similarity(l_vec, np.array(ref_vec))
                if sim > best_sim:
                    best_sim = sim
                    best_pair = (ref_lc, ref)
        if best_pair and best_sim > self.similarity_threshold:
            # Return the ref project and legacy class used as blueprint
            return {
                "reference_legacy_class": best_pair[0],
                "reference_project": best_pair[1].get("name", "unknown"),
                "similarity": best_sim
            }
        return None

# Example usage:
if __name__ == "__main__":
    # Prepare reference projects (optional)
    reference_projects = [
        {
            "name": "ref_proj_1",
            "legacy_embedding_index": json.load(open("reference_code/ref_proj_1/legacy_embedding_index.json", "r")),
            "migrated_embedding_index": json.load(open("reference_code/ref_proj_1/migrated_embedding_index.json", "r"))
        }
        # Add more as needed
    ]
    agent = ContextGraphComparatorAgent(
        legacy_dir="legacy_code/",
        migrated_dir="migrated_code/",
        reference_projects=reference_projects,
        legacy_embedding_index_path="data/legacy_embedding_index.json",
        migrated_embedding_index_path="data/embedding_index.json",
        output_path="data/context_graph_comparison.json",
        similarity_threshold=0.7,
        neighborhood_depth=2  # 1 = direct, 2 = transitive
    )
    agent.compare_graphs()


# # 1. Build context graphs & get diff report
# context_agent.compare_graphs()  # writes context_graph_comparison.json

# # 2. For each missing link in the report
# with open("data/context_graph_comparison.json") as f:
#     comparison_report = json.load(f)

# for m_class, info in comparison_report.items():
#     for missing_neighbor in info["missing_in_migrated"]:
#         # Try to fix wiring in code
#         fixed = internal_wiring_fixer_agent.try_rewire(m_class, missing_neighbor)
#         if not fixed:
#             # Try to port from legacy if allowed
#             internal_wiring_fixer_agent.try_port_legacy_class(m_class, missing_neighbor)
#         # If it's a config bean, try config fixer
#         config_wiring_fixer_agent.try_fix_bean(m_class, missing_neighbor)
#         # If it's a type mismatch, run type alignment
#         type_alignment_fixer_agent.check_and_align_types(m_class, missing_neighbor)
