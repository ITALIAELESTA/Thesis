import os
import json
from pathlib import Path

# Anchor this to the utils.py location
LIB_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = LIB_DIR.parents[1].resolve() #indicates that

def get_file_path(key):
    json_path = LIB_DIR / 'file_directories.json'
    if not json_path.exists():
        raise FileNotFoundError(f"Could not find config at {json_path}")

    with open(json_path, 'r') as f:
        paths = json.load(f)

    relative_path = paths.get(key)
    return (PROJECT_ROOT / relative_path).resolve() if relative_path else None