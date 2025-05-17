# setup.py
from setuptools import setup, find_packages

setup(
    name="migration_assist",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fire",
        "openai",
        "sentence-transformers",
        "scikit-learn",
        "javalang",
        "tiktoken",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "migration-assist=migration_assist.main:main"
        ]
    },
)
