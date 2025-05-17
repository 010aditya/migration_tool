# utils/config_loader.py
import yaml

def load_settings(path="config/settings.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)
