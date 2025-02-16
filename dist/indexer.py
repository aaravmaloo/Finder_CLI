import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


def index_folder(folder_path):
    """Indexes files in a single folder."""
    try:
        path = Path(folder_path).resolve()
        return {str(path): [f.name for f in path.iterdir() if f.is_file()]}
    except Exception as e:
        print(f"Error scanning {folder_path}: {e}")
        return {str(folder_path): []}  # Return empty if error


def index_user_directory():

    home_dir = Path.home()
    subdirs = [f for f in home_dir.iterdir() if f.is_dir()]

    file_index = {}

    with ThreadPoolExecutor(max_workers=len(subdirs)) as executor:
        results = executor.map(index_folder, subdirs)

    # Merge results
    for result in results:
        file_index.update(result)

    return file_index


# Run the scanner
file_index = index_user_directory()
if os.path.isdir(r'C:\finder_cli'):
    pass
else:
    os.mkdir(r"C:\finder_cli")


# Save results for later use (optional)
index_file = r"C:\finder_cli\index.txt"
with open(index_file, "w", encoding="utf-8") as f:
    for folder, files in file_index.items():
        f.write(f"\nFolder: {folder}\n")
        for file in files:
            f.write(f"  - {file}\n")