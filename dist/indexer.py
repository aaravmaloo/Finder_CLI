import os
import concurrent.futures


home_dir = os.path.expanduser("~")
finder_cli_dir = os.path.join(home_dir, "finder_cli")
index_file = os.path.join(finder_cli_dir, "index.txt")


os.makedirs(finder_cli_dir, exist_ok=True)


SKIP_DIRS = [
    "$recycle.bin",
    "system volume information",
    "windows",
    "program files",
    "program files (x86)",
    "drivers",
    "appdata",
    "$sysreset",
    "recovery",
    "boot",
    "perflogs",
    "msocache"
]


def main():

    base_drive = "C:\\"

    try:

        subdirs = [os.path.join(base_drive, d) for d in os.listdir(base_drive)]
        subdirs = [d for d in subdirs if os.path.isdir(d) and not any(skip in d.lower() for skip in SKIP_DIRS)]
    except PermissionError:
        subdirs = [base_drive]

    paths = []
    num_threads = max(1, os.cpu_count() // 2)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        def scan_dir(path):
            local_paths = []
            try:
                for root, dirs, files in os.walk(path):
                    try:
                        root_lower = root.lower()

                        if any(skip in root_lower for skip in SKIP_DIRS):
                            continue
                        # Add the folder itself
                        local_paths.append(f"{root}")
                        # Add all files in this folder
                        for file in files:
                            local_paths.append(os.path.join(root, file))
                    except PermissionError:
                        pass
            except PermissionError:
                pass
            return local_paths


        results = executor.map(scan_dir, subdirs)
        for result in results:
            paths.extend(result)


    with open(index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(paths))
    print(f"Indexing complete! {len(paths)} entries found (files and folders).")


if __name__ == "__main__":
    main()