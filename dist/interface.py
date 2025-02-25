import curses
import subprocess
import os
from functools import lru_cache
from colorama import Fore, Style, init
from pathlib import Path
import shutil
import shlex
from rich.tree import Tree
from rich.console import Console
import indexer

init(autoreset=True)  # colorama

@lru_cache(maxsize=128)
def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

@lru_cache(maxsize=64)
def resolve_path(path):
    return os.path.abspath(os.path.expanduser(path))

def list_dir(path="."):
    path = os.path.abspath(os.path.expanduser(path))
    tree = Tree(f"{path}")
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir():
                    tree.add(f"{entry.name}/")
                else:
                    size = entry.stat().st_size
                    tree.add(f"{entry.name} ({format_size(size)})")
    except FileNotFoundError:
        return Fore.RED + "Directory not found." + Style.RESET_ALL
    except PermissionError:
        return Fore.RED + "Permission denied." + Style.RESET_ALL
    console = Console()
    with console.capture() as capture:
        console.print(tree)
    return capture.get()

def rm(args):
    if not args:
        return Fore.RED + "Error: No filename specified."
    filename = args[0].strip()
    try:
        os.unlink(filename)
        return Fore.GREEN + f"Removed '{filename}'"
    except FileNotFoundError:
        return Fore.RED + f"File specified in stdin is not found."
    except PermissionError:
        return Fore.RED + "Permission denied by operating system."

def rmdir(args):
    if not args:
        return Fore.RED + "Error: No folder name specified."
    filename = args[0].strip()
    try:
        os.rmdir(filename)
        return Fore.GREEN + f"Removed '{filename}'"
    except FileNotFoundError:
        return Fore.RED + f"Folder specified in stdin is not found."
    except PermissionError:
        return Fore.RED + "Permission denied by operating system."

def copy_file(args):
    if len(args) < 2:
        return Fore.RED + "Error: Copy command requires source and destination."
    source, destination = args[0].strip(), args[1].strip()
    if not os.path.exists(source):
        return Fore.RED + f"Error: Source '{source}' does not exist."
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(source))
    shutil.copy(source, destination)
    return Fore.GREEN + f"Copied '{source}' to '{destination}'"

def move_file(args):
    if len(args) < 2:
        return Fore.RED + "Error: Move command requires source and destination."
    source, destination = args[0].strip(), args[1].strip()
    if not os.path.exists(source):
        return Fore.RED + f"Error: Source '{source}' does not exist."
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(source))
    shutil.move(source, destination)
    return Fore.GREEN + f"Moved '{source}' to '{destination}'"

def change_directory(args):
    if not args:
        return Fore.RED + "Error: No directory specified."
    path = args[0].strip().strip('"').strip("'")
    home_dir = os.path.expanduser("~")
    if path == "~":
        full_path = home_dir
    elif path == "*":
        full_path = os.path.join(home_dir, "Desktop")
    elif path == "!":
        full_path = os.path.join(home_dir, "Downloads")
    elif path == "&":
        full_path = os.path.join(home_dir, "AppData")
    else:
        full_path = os.path.abspath(os.path.expanduser(path))
    try:
        if not os.path.exists(full_path):
            return Fore.RED + f"Error: Path '{full_path}' does not exist."
        if not os.path.isdir(full_path):
            return Fore.RED + f"Error: '{full_path}' is not a directory."
        os.chdir(full_path)
        return Fore.GREEN + f"Changed to '{full_path}'"
    except FileNotFoundError:
        return Fore.RED + f"Directory not found: '{path}'"
    except PermissionError:
        return Fore.RED + f"Permission denied: '{path}'"
    except OSError as e:
        return Fore.RED + f"Invalid path: {e} (tried '{path}')"

def create_file(args):
    if not args:
        return Fore.RED + "Error: No filename specified."
    file_name = args[0].strip()
    try:
        Path(file_name).touch()
        return Fore.GREEN + f"Created '{file_name}'"
    except Exception as e:
        return Fore.RED + f"Error: {e}"

def show_tutorial(_):
    return """Welcome to Finder_CLI tutorial!
Finder_CLI is a command-line-based file explorer for programmers.
Basic commands include cd, ls, move, touch, and more.
Use ~ to refer to your home folder (C:\\Users\\YourName).
Press Ctrl+S to launch the indexer."""

COMMANDS = {
    "ls": lambda args: list_dir(args[0] if args else "."),
    "move": move_file,
    "cd": change_directory,
    "touch": create_file,
    "tutor": show_tutorial,
    "rm": rm,
    "rmdir": rmdir,
    "copy": copy_file,
}

def open_powershell_with_cd(path):
    command = f'powershell -NoExit -Command "Set-Location \'{path}\'"'
    subprocess.run(command, shell=True)

def main(stdscr):
    curses.curs_set(1)  # Show cursor
    stdscr.timeout(100)  # Non-blocking input with 100ms timeout
    command = ""
    output_lines = []

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Display output
        for i, line in enumerate(output_lines[-height+2:]):  # Leave room for prompt
            stdscr.addstr(i, 0, line[:width-1])

        # Display prompt and command
        prompt = f"{os.getcwd()}> {command}"
        stdscr.addstr(height-1, 0, prompt[:width-1])
        stdscr.move(height-1, min(len(prompt), width-1))

        stdscr.refresh()

        # Get key input
        key = stdscr.getch()
        if key == -1:  # No key pressed
            continue

        if key == 19:  # Ctrl+S (ASCII 19)
            stdscr.clear()
            stdscr.addstr(0, 0, "Launching indexer...")
            stdscr.refresh()
            indexer.main(stdscr)  # Call indexer.main directly with stdscr
            continue

        elif key == 27:  # ESC
            break

        elif key == 10:  # Enter
            if command.strip():
                if command.strip() == "cd..":
                    os.chdir("..")
                    output_lines.append(Fore.GREEN + f"Changed to '{os.getcwd()}'")
                else:
                    try:
                        parts = shlex.split(command, posix=False)
                        cmd = parts[0]
                        args = parts[1:] if len(parts) > 1 else []
                        if cmd in COMMANDS:
                            result = COMMANDS[cmd](args)
                            if result:
                                output_lines.append(result)
                        else:
                            output_lines.append(Fore.RED + "Invalid command.")
                    except ValueError:
                        output_lines.append(Fore.RED + "Error: Invalid command syntax (check quotes).")
                command = ""

        elif key in (curses.KEY_BACKSPACE, 127, 8):  # Backspace
            if command:
                command = command[:-1]

        elif 32 <= key <= 126:  # Printable characters
            command += chr(key)

    # On exit, open PowerShell
    working_dir = os.getcwd()
    open_powershell_with_cd(working_dir)

if __name__ == "__main__":
    curses.wrapper(main)