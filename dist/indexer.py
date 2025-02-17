import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

HOME_DIR = Path.home()
EXCLUDED_FOLDERS = {"AppData"}

def index_folder(folder_path):

    try:
        path = Path(folder_path).resolve()
        file_list = []
        subfolders = []

        for f in path.iterdir():
            try:
                if f.is_file():
                    file_list.append(f.name)
                elif f.is_dir() and f.name not in EXCLUDED_FOLDERS:
                    subfolders.append(f)
            except PermissionError:
               pass


        # Recursively index subfolders
        file_index = {str(path): file_list}

        with ThreadPoolExecutor() as executor:
            results = executor.map(index_folder, subfolders)
            for result in results:
                file_index.update(result)

        return file_index
    except PermissionError:
        pass
        return {str(folder_path): []}
    except Exception as e:
        print(f"Error scanning {folder_path}: {e}")
        return {str(folder_path): []}

def index_home_directory():

    subdirs = [f for f in HOME_DIR.iterdir() if f.is_dir() and f.name not in EXCLUDED_FOLDERS]
    file_index = {}

    with ThreadPoolExecutor(max_workers=len(subdirs)) as executor:
        results = executor.map(index_folder, subdirs)

    for result in results:
        file_index.update(result)

    return file_index

# Run the scanner
file_index = index_home_directory()


index_dir = Path(r"C:\\Users\\Aarav Maloo\\finder_cli")
index_dir.mkdir(exist_ok=True)

# Save results
index_file = index_dir / "index.txt"
with open(index_file, "w", encoding="utf-8") as f:
    for folder, files in file_index.items():
        f.write(f"\nFolder: {folder}\n")
        for file in files:
            f.write(f"  - {file}\n")

print(f"Indexing complete! Results saved to {index_file}")


