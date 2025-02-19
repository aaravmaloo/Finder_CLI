import os
import concurrent.futures


home_dir = os.path.expanduser("~")
finder_cli_dir = os.path.join(home_dir, "finder_cli")
index_file = os.path.join(finder_cli_dir, "index.txt")


os.makedirs(finder_cli_dir, exist_ok=True)


def scan_directory(path):

    file_paths = []
    for root, _, files in os.walk(path):
        # Skip AppData directory
        if "AppData" in root:
            continue

        for file in files:
            file_paths.append(os.path.join(root, file))

    return file_paths


def threaded_scan():
    subdirs = [os.path.join(home_dir, d) for d in os.listdir(home_dir)]
    subdirs = [d for d in subdirs if os.path.isdir(d) and "AppData" not in d]  # Exclude AppData

    file_paths = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(scan_directory, subdirs)

        for result in results:
            file_paths.extend(result)

    return file_paths


if __name__ == "__main__":
    print(f"Scanning your home directory: {home_dir} using 5 threads... (Skipping AppData)")
    all_files = threaded_scan()

    with open(index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_files))

    print(f"Scan complete! Indexed {len(all_files)} files.")
    print(f"Index saved at: {index_file}")
