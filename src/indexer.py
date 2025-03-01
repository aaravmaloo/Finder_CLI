# indexer.py
import os
import platform
from rich.console import Console
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

CONSOLE = Console()

home_dir = os.path.expanduser("~")
finder_cli_dir = os.path.join(home_dir, "finder_cli")
index_file = os.path.join(finder_cli_dir, "index.txt")

os.makedirs(finder_cli_dir, exist_ok=True)

if platform.system() == "Windows":
    SKIP_DIRS = [
        "$recycle.bin", "system volume information", "windows",
        "program files", "program files (x86)", "drivers", "appdata",
        "$sysreset", "recovery", "boot", "perflogs", "msocache"
    ]
elif platform.system() == "Darwin":  # macOS
    SKIP_DIRS = [
        "system", "library", "private", "cores", "volumes",
        "dev", "tmp", "var", "bin", "sbin"
    ]
else:
    raise OSError("This script only supports Windows and macOS.")

def index_files():
    base_path = "C:\\" if platform.system() == "Windows" else "/"
    paths = []
    try:
        for root, dirs, files in os.walk(base_path):
            root_lower = root.lower()
            if any(skip in root_lower for skip in SKIP_DIRS):
                continue
            paths.append(root)
            for file in files:
                paths.append(os.path.join(root, file))
    except PermissionError:
        CONSOLE.print("Permission denied in some directories; indexed accessible areas only.", style="yellow")

    with open(index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(paths))
    return paths

def load_items():
    if not os.path.exists(index_file):
        return []
    with open(index_file, "r", encoding="utf-8") as f:
        full_paths = f.read().splitlines()
    return [(os.path.basename(path), path) for path in full_paths]

class IndexerApp:
    def __init__(self):
        self.items = load_items()
        self.selected_idx = 0

        # Buffer for user input
        self.buffer = Buffer(on_text_changed=self.update_results)

        # Display area for results
        self.results_control = FormattedTextControl(self.get_results_text)
        self.results_window = Window(content=self.results_control, height=20)

        # Inline prompt and input
        self.prompt_control = FormattedTextControl(self.get_prompt_text)
        self.input_window = Window(content=BufferControl(buffer=self.buffer), height=1)

        # Layout
        self.root_container = HSplit([
            self.results_window,
            Window(content=self.prompt_control, height=1),  # Prompt and input on same line
        ])
        self.layout = Layout(self.root_container)

        # Key bindings
        bindings = KeyBindings()

        @bindings.add('escape')  # ESC to exit
        def _(event):
            event.app.exit()

        @bindings.add('up')  # Up arrow
        def _(event):
            self.selected_idx = max(0, self.selected_idx - 1)
            self.update_display()

        @bindings.add('down')  # Down arrow
        def _(event):
            filtered = self.get_filtered_items()
            if filtered:
                self.selected_idx = min(len(filtered) - 1, self.selected_idx + 1)
            self.update_display()

        @bindings.add('enter')  # Enter to open
        def _(event):
            filtered = self.get_filtered_items()
            if filtered and self.selected_idx < len(filtered):
                _, full_path = filtered[self.selected_idx]
                try:
                    if platform.system() == "Windows":
                        os.startfile(full_path)
                    elif platform.system() == "Darwin":
                        os.system(f"open '{full_path}'")
                except Exception as e:
                    CONSOLE.print(f"Error: {e}", style="red")
            self.update_display()

        # Application
        self.app = Application(
            layout=self.layout,
            key_bindings=bindings,
            full_screen=False,
        )

    def get_filtered_items(self):
        query = self.buffer.text.strip().lower()
        if not query:
            return self.items
        return [(name, path) for name, path in self.items if query in name.lower()]

    def get_results_text(self):
        filtered = self.get_filtered_items()
        if not filtered:
            return [("yellow", "No matches found.")]
        lines = []
        self.selected_idx = max(0, min(self.selected_idx, len(filtered) - 1))
        for i, (name, _) in enumerate(filtered[:20]):  # Limit to 20 items
            if i == self.selected_idx:
                lines.append(("bold green", f"> {name}"))
            else:
                lines.append(("white", f"{name}"))
            lines.append(("", "\n"))  # Newline after each item
        return lines

    def get_prompt_text(self):
        return [("white", f"Find> {self.buffer.text}")]

    def update_results(self, buffer):
        self.update_display()

    def update_display(self):
        self.results_control.text = self.get_results_text()
        self.prompt_control.text = self.get_prompt_text()
        self.app.invalidate()  # Force redraw

    def run(self):
        self.app.run()

def main():
    CONSOLE.print("Checking index...", style="yellow")
    if not os.path.exists(index_file):
        CONSOLE.print("Creating initial index (this may take a moment)...", style="yellow")
        index_files()
        CONSOLE.print("Index created!", style="green")

    items = load_items()
    if not items:
        CONSOLE.print("No items indexed. Try running with sudo if on macOS.", style="red")
        return

    app = IndexerApp()
    app.run()

if __name__ == "__main__":
    main()