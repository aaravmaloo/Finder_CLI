import keyboard
import os
import indexer















if __name__ == "__main__":
    print(f"Scanning your home directory: {indexer.home_dir} using 5 threads... (Skipping AppData)")
    all_files = indexer.threaded_scan()

    with open(indexer.index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_files))

    print(f"Scan complete! Indexed {len(all_files)} files.")
    print(f"Index saved at: {indexer.index_file}")
