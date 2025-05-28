import javalang
import os
import json

def build_legacy_relationship_graph(legacy_dir, output_path):
    relationship_graph = {}
    for root, dirs, files in os.walk(legacy_dir):
        for file in files:
            if file.endswith(".java"):
                fpath = os.path.join(root, file)
                with open(fpath, encoding="utf-8") as f:
                    code = f.read()
                try:
                    tree = javalang.parse.parse(code)
                    class_name = None
                    related = set()
                    for node in tree.types:
                        if isinstance(node, javalang.tree.ClassDeclaration):
                            class_name = node.name
                            # Field dependencies
                            for field in node.fields:
                                if field.type and hasattr(field.type, 'name'):
                                    related.add(field.type.name)
                            # Constructor and method parameters
                            for ctor in node.constructors:
                                for p in ctor.parameters:
                                    if p.type and hasattr(p.type, 'name'):
                                        related.add(p.type.name)
                            for m in node.methods:
                                for p in m.parameters:
                                    if p.type and hasattr(p.type, 'name'):
                                        related.add(p.type.name)
                                # Direct method invocations
                                for path, inv in m.filter(javalang.tree.MethodInvocation):
                                    if inv.qualifier:
                                        related.add(inv.qualifier)
                            if class_name:
                                relationship_graph[class_name] = list(related)
                except Exception as e:
                    print(f"[WARN] Could not parse {fpath}: {e}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(relationship_graph, f, indent=2)
    print(f"Legacy relationship graph saved to {output_path}")

if __name__ == "__main__":
    # Example usage:
    build_legacy_relationship_graph(
        legacy_dir="legacy_code/",
        output_path="data/legacy_relationships.json"
    )
