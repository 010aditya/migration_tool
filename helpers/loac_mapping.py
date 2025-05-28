import json
import os
import re

def get_class_name_from_path(path):
    # Extract class name from file path
    return os.path.splitext(os.path.basename(path))[0]

def load_mapping(mapping_path):
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    legacy_to_migrated = {}
    migrated_to_legacy = {}
    for entry in mapping:
        for src_path in entry["source"]:
            src_class = get_class_name_from_path(src_path)
            tgt_classes = [get_class_name_from_path(p) for p in entry["target"]]
            if src_class in legacy_to_migrated:
                legacy_to_migrated[src_class].extend(tgt_classes)
            else:
                legacy_to_migrated[src_class] = tgt_classes
            for tgt_class in tgt_classes:
                if tgt_class in migrated_to_legacy:
                    migrated_to_legacy[tgt_class].append(src_class)
                else:
                    migrated_to_legacy[tgt_class] = [src_class]
    return legacy_to_migrated, migrated_to_legacy


def parse_build_log(build_log_path):
    broken_classes = set()
    with open(build_log_path, encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "error: cannot find symbol" in line:
            # Look ahead for "class FooBar"
            for j in range(1, 3):
                if i + j < len(lines) and "class" in lines[i + j]:
                    parts = lines[i + j].strip().split()
                    if len(parts) >= 3:
                        broken_classes.add(parts[-1])
    return broken_classes
