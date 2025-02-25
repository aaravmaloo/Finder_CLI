import curses
import subprocess
import os
from functools import lru_cache
from pathlib import Path
import shutil
import shlex
from rich.tree import Tree
from rich.console import Console
import indexer

def init_colors():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)

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

def list_dir(args):
    path = args[0] if args else "."
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
        return ["Directory not found."], COLOR_RED
    except PermissionError:
        return ["Permission denied."], COLOR_RED
    console = Console()
    with console.capture() as capture:
        console.print(tree)
    return capture.get().splitlines(), COLOR_DEFAULT

def rm(args):
    if not args:
        return ["Error: No filename specified."], COLOR_RED
    filename = args[0].strip()
    try:
        os.unlink(filename)
        return [f"Removed '{filename}'"], COLOR_GREEN
    except FileNotFoundError:
        return [f"File specified in stdin is not found."], COLOR_RED
    except PermissionError:
        return ["Permission denied by operating system."], COLOR_RED

def rmdir(args):
    if not args:
        return ["Error: No folder name specified."], COLOR_RED
    filename = args[0].strip()
    try:
        os.rmdir(filename)
        return [f"Removed '{filename}'"], COLOR_GREEN
    except FileNotFoundError:
        return [f"Folder specified in stdin is not found."], COLOR_RED
    except PermissionError:
        return ["Permission denied by operating system."], COLOR_RED

def copy_file(args):
    if len(args) < 2:
        return ["Error: Copy command requires source and destination."], COLOR_RED
    source, destination = args[0].strip(), args[1].strip()
    if not os.path.exists(source):
        return [f"Error: Source '{source}' does not exist."], COLOR_RED
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(source))
    try:
        shutil.copy(source, destination)
        return [f"Copied '{source}' to '{destination}'"], COLOR_GREEN
    except Exception as e:
        return [f"Error: {e}"], COLOR_RED

def move_file(args):
    if len(args) < 2:
        return ["Error: Move command requires source and destination."], COLOR_RED
    source, destination = args[0].strip(), args[1].strip()
    if not os.path.exists(source):
        return [f"Error: Source '{source}' does not exist."], COLOR_RED
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(source))
    try:
        shutil.move(source, destination)
        return [f"Moved '{source}' to '{destination}'"], COLOR_GREEN
    except Exception as e:
        return [f"Error: {e}"], COLOR_RED

def change_directory(args):
    if not args:
        return ["Error: No directory specified."], COLOR_RED
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
            return [f"Error: Path '{full_path}' does not exist."], COLOR_RED
        if not os.path.isdir(full_path):
            return [f"Error: '{full_path}' is not a directory."], COLOR_RED
        os.chdir(full_path)
        return [f"Changed to '{full_path}'"], COLOR_GREEN
    except FileNotFoundError:
        return [f"Directory not found: '{path}'"], COLOR_RED
    except PermissionError:
        return [f"Permission denied: '{path}'"], COLOR_RED
    except OSError as e:
        return [f"Invalid path: {e} (tried '{path}')"], COLOR_RED

def create_file(args):
    if not args:
        return ["Error: No filename specified."], COLOR_RED
    file_name = args[0].strip()
    try:
        Path(file_name).touch()
        return [f"Created '{file_name}'"], COLOR_GREEN
    except Exception as e:
        return [f"Error: {e}"], COLOR_RED

def show_tutorial(_):
    return ["Welcome to Finder_CLI tutorial!",
            "Finder_CLI is a command-line-based file explorer for programmers.",
            "Basic commands include cd, ls, move, touch, and more.",
            "Use ~ to refer to your home folder (C:\\Users\\YourName).",
            "Press Ctrl+S to launch the indexer."], COLOR_DEFAULT

def clear_output(_):
    return [], COLOR_DEFAULT

COMMANDS = {
    "ls": list_dir,
    "move": move_file,
    "cd": change_directory,
    "touch": create_file,
    "tutor": show_tutorial,
    "rm": rm,
    "rmdir": rmdir,
    "copy": copy_file,
    "clear": clear_output,
}

def open_powershell_with_cd(path):
    command = f'powershell -NoExit -Command "Set-Location \'{path}\'"'
    subprocess.run(command, shell=True)

def main(stdscr):

    init_colors()
    global COLOR_RED, COLOR_GREEN, COLOR_DEFAULT
    COLOR_RED = curses.color_pair(1)
    COLOR_GREEN = curses.color_pair(2)
    COLOR_DEFAULT = curses.color_pair(3)


    for func in COMMANDS.values():
        func.__globals__.update({
            "COLOR_RED": COLOR_RED,
            "COLOR_GREEN": COLOR_GREEN,
            "COLOR_DEFAULT": COLOR_DEFAULT
        })

    curses.curs_set(1)
    stdscr.timeout(100)
    command = ""
    output_lines = []
    command_history = []
    history_index = -1

    while True:
        stdscr.clear()  # Clear the entire screen each loop
        height, width = stdscr.getmaxyx()


        max_output_lines = height - 2
        for i, (line, color) in enumerate(output_lines[-max_output_lines:]):
            stdscr.addstr(i, 0, line[:width-1], color)


        prompt = f"[finder_cli] {os.getcwd()}> {command}"
        stdscr.addstr(height-1, 0, prompt[:width-1], COLOR_DEFAULT)
        stdscr.move(height-1, min(len(prompt), width-1))

        stdscr.refresh()


        key = stdscr.getch()
        if key == -1:
            continue

        if key == 19:
            stdscr.clear()
            stdscr.addstr(0, 0, "Launching indexer...", COLOR_DEFAULT)
            stdscr.refresh()
            indexer.main(stdscr)
            stdscr.clear()
            continue

        elif key == 27:  # ESC
            break

        elif key == 10:  # Enter
            if command.strip():
                command_history.append(command.strip())
                history_index = -1
                if command.strip() == "cd..":
                    os.chdir("..")
                    output_lines.append((f"Changed to '{os.getcwd()}'", COLOR_GREEN))
                else:
                    try:
                        parts = shlex.split(command, posix=False)
                        cmd = parts[0]
                        args = parts[1:] if len(parts) > 1 else []
                        if cmd in COMMANDS:
                            result, color = COMMANDS[cmd](args)
                            if not result:
                                output_lines = []
                            elif result:
                                output_lines.extend((line, color) for line in result)
                        else:
                            output_lines.append(("Invalid command.", COLOR_RED))
                    except ValueError as e:
                        output_lines.append((f"Error: Invalid command syntax - {str(e)}", COLOR_RED))
                    except Exception as e:
                        output_lines.append((f"Error: {str(e)}", COLOR_RED))
                command = ""

        elif key in (curses.KEY_BACKSPACE, 127, 8):  #
            if command:
                command = command[:-1]

        elif key == curses.KEY_UP:
            if command_history and history_index < len(command_history) - 1:
                history_index += 1
                command = command_history[len(command_history) - 1 - history_index]

        elif key == curses.KEY_DOWN:
            if history_index > -1:
                history_index -= 1
                if history_index == -1:
                    command = ""
                else:
                    command = command_history[len(command_history) - 1 - history_index]

        elif 32 <= key <= 126:
            command += chr(key)


    working_dir = os.getcwd()
    open_powershell_with_cd(working_dir)

if __name__ == "__main__":
    curses.wrapper(main)