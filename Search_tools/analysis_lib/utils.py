import os
import json
import shutil
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

def move_file(source_file, destination_folder):
    # Ensure inputs are Path objects
    source = Path(source_file)
    dest_dir = Path(destination_folder)

    # 1. Create the destination directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 2. Define the full destination path (folder + filename)
    destination_path = dest_dir / source.name

    # 3. Move the file
    # .replace() is efficient but will overwrite existing files.
    # We use source.rename() or shutil.move for cross-filesystem safety.
    if destination_folder is None:
        print(f"No destination folder specified")
    else:
        try:
            source.rename(destination_path)

            print(f"Moved: {source.name} -> {dest_dir}")
        except FileExistsError:
            print("File already exists")
        except FileNotFoundError:
            print("File does not exist")