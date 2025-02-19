import keyboard
import os
import indexer















if __name__ == "__main__":

    all_files = indexer.threaded_scan()

    with open(indexer.index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_files))


