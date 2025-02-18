import os
import time
import servicemanager
import win32serviceutil
import win32service
import win32event
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

HOME_DIR = Path.home()
EXCLUDED_FOLDERS = {"AppData"}
INDEX_FILE_PATH = HOME_DIR / "index.txt"  # Store index in the home folder


class DirectoryIndexHandler(FileSystemEventHandler):
    def __init__(self, file_index):
        self.file_index = file_index

    def on_any_event(self, event):
        if event.is_directory:
            self.update_index(event.src_path)

    def update_index(self, folder_path):
        new_index = index_folder(Path(folder_path))
        self.file_index.update(new_index)
        self.save_index_to_file()

    def save_index_to_file(self):
        with open(INDEX_FILE_PATH, "w", encoding="utf-8") as f:
            for folder, files in self.file_index.items():
                f.write(f"\nFolder: {folder}\n")
                for file in files:
                    f.write(f"  - {file}\n")


def create_initial_index_file():
    # Create the index file if it doesn't exist
    if not INDEX_FILE_PATH.exists():
        with open(INDEX_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("Initial Index File\n")


def index_folder(folder_path):
    try:
        path = Path(folder_path).resolve()
        file_list = []
        subfolders = []

        for f in path.iterdir():
            if f.is_file():
                file_list.append(f.name)
            elif f.is_dir() and f.name not in EXCLUDED_FOLDERS:
                subfolders.append(f)

        file_index = {str(path): file_list}

        with ThreadPoolExecutor() as executor:
            results = executor.map(index_folder, subfolders)
            for result in results:
                file_index.update(result)

        return file_index
    except Exception as e:
        print(f"Error scanning {folder_path}: {e}")
        return {str(folder_path): []}


class FinderIndexerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "finder_indexer"
    _svc_display_name_ = "Finder Indexer Service"
    _svc_description_ = "Finder_ClIs service to monitor file changes and save for fast searching and dir lookup."

    def __init__(self, args):
        super().__init__(args)
        self.halt_event = win32event.CreateEvent(None, 0, 0, None)
        self.observer = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.observer:
            self.observer.stop()
            self.observer.join()
        win32event.SetEvent(self.halt_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        # Create the index file at service start if it doesn't exist
        create_initial_index_file()

        # Index the home folder at startup and save the index to the file
        file_index = index_folder(HOME_DIR)
        event_handler = DirectoryIndexHandler(file_index)

        # Save the initial index to the file
        event_handler.save_index_to_file()

        # Set up the file system observer to monitor changes
        self.observer = Observer()
        self.observer.schedule(event_handler, str(HOME_DIR), recursive=True)
        self.observer.start()

        servicemanager.LogInfoMsg("Finder Indexer Service Started")

        while True:
            if win32event.WaitForSingleObject(self.halt_event, 5000) == win32event.WAIT_OBJECT_0:
                break


win32serviceutil.HandleCommandLine(FinderIndexerService)
if __name__ == "__main__":
    pass
