import os
import curses
import platform
import time
import threading
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import platform
import ctypes

FINDER_CLI_PATH = "~/.finder_cli"
IS_IGNORING_DOT_FILE = True
# in secounds
EVENT_TIME_DIFF = 10

finder_cli_dir = os.path.expanduser("finder_cli")
index_file = os.path.join(finder_cli_dir, "index.txt")

os.makedirs(finder_cli_dir, exist_ok=True)

SKIP_DIRS = [
    ".git",
    "node_modules",
    "__pycache__",
    "env",  # Commone python virtual environment
    "venv",  # Commone python virtual environment
    "dist",  # Distribution directory
    "build",
    "out",
    "target",  # Maven target
    "bundle",  # Ruby bundle
    "log",  # Log files
    "tmp",  # Temporary files
    "temp",
    "deps",
    "Pods",  # CocoaPods
    " Carthage",  # Carthage
    "vendor",
    "bundle",
    "storage",  # Laravel Storage
    "generated",
    "cache",
    "caches",
]

# Platform-specific skip directories
if platform.system() == "Windows":
    SKIP_DIRS.extend(
        [
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
            "msocache",
        ]
    )
else:  # Linux/Unix
    SKIP_DIRS.extend(
        [
            "proc",
            "sys",
            "dev",
            "tmp",
            "var",
            "run",
            "boot",
            "root",
            "sbin",
            "bin",
            "lib",
            "lib64",
        ]
    )

index_queue = queue.Queue()


def get_base_path():
    """Gets the current drive letter on Windows, or '/' on other systems."""
    if platform.system() == "Windows":
        return os.path.splitdrive(os.getcwd())[0] + "\\"
    else:
        return "/"


class IndexHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_event = 0

    def on_any_event(self, event):
        if event.src_path.endswith("index.txt") or event.src_path.startswith("~$"):
            return

        if current_time - self.last_event > EVENT_TIME_DIFF:
            if event.event_type == "deleted":
                index_queue.put(("remove", event.src_path))
            else:
                index_queue.put("reindex")
            self.last_event = current_time


def index_files(background=False):
    import concurrent.futures

    base_path = get_base_path()
    try:
        subdirs = [os.path.join(base_path, d) for d in os.listdir(base_path)]
        subdirs = [
            d
            for d in subdirs
            if os.path.isdir(d) and not any(skip in d.lower() for skip in SKIP_DIRS)
        ]
    except PermissionError:
        subdirs = [base_path]

    paths = []
    num_threads = max(1, os.cpu_count() or 2 // 2)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:

        def scan_dir(path):
            local_paths = []
            try:
                for root, dirs, files in os.walk(path):
                    try:
                        root_lower = root.lower()
                        if any(skip in root_lower for skip in SKIP_DIRS):
                            continue
                        local_paths.append(f"{root}")
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

    if background:
        index_queue.put("index_complete")


def remove_path_from_index(path_to_remove):
    if not os.path.exists(index_file):
        return

    with open(index_file, "r", encoding="utf-8") as f:
        paths = f.read().splitlines()

    paths = [p for p in paths if p != path_to_remove]

    with open(index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(paths))


def background_indexer():
    while True:
        msg = index_queue.get()
        if isinstance(msg, tuple) and msg[0] == "remove":
            remove_path_from_index(msg[1])
        elif msg == "reindex":
            index_files(background=True)
        elif msg == "stop":
            break


def load_items():
    if not os.path.exists(index_file):
        return []
    with open(index_file, "r", encoding="utf-8") as f:
        full_paths = f.read().splitlines()
    return [(os.path.basename(path), path) for path in full_paths]


def main(stdscr):
    # Use root path based on platform
    root_path = "C:\\" if platform.system() == "Windows" else "/"

    if not os.path.exists(index_file):
        stdscr.addstr(1, 2, "Creating initial index...")
        stdscr.refresh()
        index_files()
        stdscr.addstr(2, 2, "Index created!")
        stdscr.refresh()
        time.sleep(1)

    indexer_thread = threading.Thread(target=background_indexer, daemon=True)
    indexer_thread.start()

    items = load_items()
    indexing_status = ""

    event_handler = IndexHandler()
    observer = Observer()
    observer.schedule(event_handler, root_path, recursive=True)
    observer.start()
    stdscr.nodelay(False)

    try:
        curses.curs_set(1)
        query = ""
        selected_idx = 0

        while True:
            try:
                msg = index_queue.get_nowait()
                if isinstance(msg, tuple) and msg[0] == "remove":
                    items = load_items()
                    indexing_status = f"Removed: {os.path.basename(msg[1])}"
                elif msg == "index_complete":
                    items = load_items()
                    indexing_status = "Index updated"
                    threading.Timer(
                        2.0, lambda: globals().update(indexing_status="")
                    ).start()
                elif msg == "reindex":
                    indexing_status = "Indexing..."
            except queue.Empty:
                pass

            stdscr.clear()
            height, width = stdscr.getmaxyx()
            max_display = height - 3

            if query:
                filtered = [
                    (name, path)
                    for name, path in items
                    if query.lower() in name.lower()
                ]
            else:
                filtered = items

            if not filtered:
                selected_idx = 0
            else:
                selected_idx = max(0, min(selected_idx, len(filtered) - 1))

            for i, (name, _) in enumerate(filtered[:max_display]):
                display_name = name[: width - 1]
                if i == selected_idx:
                    stdscr.addstr(i, 0, display_name, curses.A_REVERSE)
                else:
                    stdscr.addstr(i, 0, display_name)

            if indexing_status:
                stdscr.addstr(height - 2, 0, indexing_status[: width - 1])

            prompt = f"Find> {query}"
            stdscr.addstr(height - 1, 0, prompt[: width - 1])
            stdscr.move(height - 1, min(len(prompt), width - 1))
            stdscr.refresh()

            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if query:
                    query = query[:-1]
                    selected_idx = 0
            elif 32 <= key <= 126:
                query += chr(key)
                selected_idx = 0
            elif key == curses.KEY_UP:
                selected_idx = max(0, selected_idx - 1)
            elif key == curses.KEY_DOWN:
                if filtered:
                    selected_idx = min(len(filtered) - 1, selected_idx + 1)
            elif key == 10:
                if filtered:
                    _, full_path = filtered[selected_idx]
                    try:
                        if platform.system() == "Windows":
                            os.startfile(full_path)
                        elif platform.system() == "Linux":
                            os.system(f"xdg-open '{full_path}'")
                        elif platform.system() == "Darwin":
                            os.system(f"open '{full_path}'")
                    except Exception as e:
                        stdscr.addstr(height - 3, 0, f"Error: {str(e)}"[: width - 1])
                        stdscr.refresh()
                        stdscr.getch()

    finally:
        index_queue.put("stop")
        observer.stop()
        observer.join()


def run():
    curses.wrapper(main)


if __name__ == "__main__":
    run()
