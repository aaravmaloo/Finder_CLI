import os
import concurrent.futures

# Define the base directory for Finder CLI
home_dir = os.path.expanduser("~")
finder_cli_dir = os.path.join(home_dir, "finder_cli")
index_file = os.path.join(finder_cli_dir, "index.txt")

# Ensure the directory exists
os.makedirs(finder_cli_dir, exist_ok=True)

# List of directories to skip
SKIP_DIRS = ["$recycle.bin", "system volume information", "windows", "program files", "drivers", "appdata"]

def main():
    base_drive = "C:\\" if os.name == "nt" else "/"
    try:
        subdirs = [os.path.join(base_drive, d) for d in os.listdir(base_drive)]
        subdirs = [d for d in subdirs if os.path.isdir(d) and not any(skip in d.lower() for skip in SKIP_DIRS)]
    except PermissionError:
        subdirs = [base_drive]

    file_paths = []
    num_threads = max(1, os.cpu_count() // 2)
    print(f"Using {num_threads} threads for scanning...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        def scan_dir(path):
            paths = []
            try:
                for root, _, files in os.walk(path):
                    try:
                        root_lower = root.lower()
                        if any(skip in root_lower for skip in SKIP_DIRS):
                            continue
                        for file in files:
                            paths.append(os.path.join(root, file))
                    except PermissionError:
                        pass
            except PermissionError:
                pass
            return paths

        results = executor.map(scan_dir, subdirs)
        for result in results:
            file_paths.extend(result)

    with open(index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(file_paths))
    print(f"Indexing complete! {len(file_paths)} files found.")

if __name__ == "__main__":
    main()