# error_classifier.py

import re

class ErrorClassifier:
    def __init__(self):
        self.patterns = [
            (re.compile(r"error: cannot find symbol"), "unresolved_symbol"),
            (re.compile(r"package .* does not exist"), "missing_import"),
            (re.compile(r"error: cannot access .*"), "missing_dependency"),
            (re.compile(r"method .* not found"), "missing_method"),
            (re.compile(r"incompatible types"), "type_mismatch"),
            (re.compile(r"class .* is public, should be declared in a file named"), "filename_class_mismatch"),
            (re.compile(r"class, interface, or enum expected"), "syntax_error"),
            (re.compile(r"duplicate class: .*"), "duplicate_class"),
            (re.compile(r"package declaration does not match file path"), "package_mismatch"),
        ]

    def classify(self, build_log):
        errors = set()
        for line in build_log.splitlines():
            for pattern, label in self.patterns:
                if pattern.search(line):
                    errors.add(label)
        return list(errors)
