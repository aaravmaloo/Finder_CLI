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



COLOR_RED = 1
COLOR_GREEN = 2
COLOR_DEFAULT = 3


CONSOLE = Console()


SHORTCUT_REPLACEMENTS = {
    "~": os.path.expanduser("~"),
    "*": os.path.join(os.path.expanduser("~"), "Desktop"),
    "!": os.path.join(os.path.expanduser("~"), "Downloads"),
    "&": os.path.join(os.path.expanduser("~"), "AppData")
}

def init_colors():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    global COLOR_RED, COLOR_GREEN, COLOR_DEFAULT
    COLOR_RED = curses.color_pair(1)
    COLOR_GREEN = curses.color_pair(2)
    COLOR_DEFAULT = curses.color_pair(3)

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
    path = resolve_path(args[0] if args else ".")
    tree = Tree(f"{path}")
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                name = entry.name
                tree.add(f"{name}/" if entry.is_dir() else f"{name} ({format_size(entry.stat().st_size)})")
        with CONSOLE.capture() as capture:
            CONSOLE.print(tree)
        return capture.get().splitlines(), COLOR_DEFAULT
    except FileNotFoundError:
        return ["Directory not found."], COLOR_RED
    except PermissionError:
        return ["Permission denied."], COLOR_RED




def rm(args):
    if not args:
        return ["Error: No filename specified."], COLOR_RED
    filename = args[0].strip()
    try:
        os.unlink(filename)
        return [f"Removed '{filename}'"], COLOR_GREEN
    except FileNotFoundError:
        return ["File specified in stdin is not found."], COLOR_RED
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
        return ["Folder specified in stdin is not found."], COLOR_RED
    except PermissionError:
        return ["Permission denied by operating system."], COLOR_RED

def make_directory(args):
    if not args:
        return ["Error: No directory name specified."], COLOR_RED
    dir_name = args[0].strip()
    try:
        os.mkdir(dir_name)
        return [f"Created directory '{dir_name}'"], COLOR_GREEN
    except FileExistsError:
        return [f"Error: Directory '{dir_name}' already exists."], COLOR_RED
    except PermissionError:
        return ["Permission denied by operating system."], COLOR_RED
    except OSError as e:
        return [f"Error: {e}"], COLOR_RED

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
    full_path = path
    for shortcut, replacement in SHORTCUT_REPLACEMENTS.items():
        if full_path.startswith(shortcut):
            full_path = full_path.replace(shortcut, replacement, 1)
            break
    full_path = os.path.abspath(os.path.expanduser(full_path))
    try:
        if not os.path.isdir(full_path):
            return [f"Error: '{full_path}' is not a directory or does not exist."], COLOR_RED
        os.chdir(full_path)
        return [f"Changed to '{full_path}'"], COLOR_GREEN
    except PermissionError:
        return [f"Permission denied: '{path}'"], COLOR_RED
    except OSError as e:
        return [f"Invalid path: {e}"], COLOR_RED

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
            "Basic commands: cd, ls, move, touch, etc.",
            "Use ~ for home folder (C:\\Users\\YourName).",
            "Press Ctrl+S to launch indexer."], COLOR_DEFAULT


def clear_output(_):
    return [], COLOR_DEFAULT

COMMANDS = {
    "ls": list_dir, "move": move_file, "cd": change_directory,
    "touch": create_file, "tutor": show_tutorial, "rm": rm,
    "rmdir": rmdir, "copy": copy_file, "clear": clear_output,
    "cls": clear_output, "dir": list_dir, "mkdir" : make_directory,
}

def open_powershell_with_cd(path):
    subprocess.run(f'powershell -NoExit -Command "Set-Location \'{path}\'"', shell=True)

def main(stdscr):
    init_colors()
    curses.curs_set(1)
    stdscr.timeout(20)
    stdscr.nodelay(True)
    command = ""
    output_lines = []
    command_history = []
    history_index = -1
    cursor_pos = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        max_output_lines = height - 2


        for i, (line, color) in enumerate(output_lines[-max_output_lines:]):
            if i < height - 1:
                stdscr.addstr(i, 0, line[:width - 1], color)

        prompt = f"[finder_cli] {os.getcwd()}> {command}"
        stdscr.addstr(height - 1, 0, prompt[:width - 1], COLOR_DEFAULT)
        stdscr.move(height - 1, min(len(f"[finder_cli] {os.getcwd()}> ") + cursor_pos, width - 1))

        stdscr.refresh()

        key = stdscr.getch()
        if key == -1:
            continue

        if key == 19:
            stdscr.clear()
            stdscr.addstr(0, 0, "[indexer] ", COLOR_DEFAULT)
            stdscr.refresh()
            indexer.main(stdscr)
            continue

        elif key == 27:
            break

        elif key == 10:
            cmd = command.strip()
            if cmd:
                command_history.append(cmd)
                history_index = -1
                if cmd == "cd..":
                    os.chdir("..")
                    output_lines.append((f"Changed to '{os.getcwd()}'", COLOR_GREEN))
                else:
                    try:
                        parts = shlex.split(cmd, posix=False)
                        cmd_name, args = parts[0], parts[1:] if len(parts) > 1 else []
                        if cmd_name in COMMANDS:
                            result, color = COMMANDS[cmd_name](args)
                            output_lines = result if not result else output_lines + [(line, color) for line in result]
                        else:
                            output_lines.append(("Invalid command.", COLOR_RED))
                    except ValueError as e:
                        output_lines.append((f"Error: Invalid command syntax - {e}", COLOR_RED))
                    except Exception as e:
                        output_lines.append((f"Error: {e}", COLOR_RED))
                command = ""
                cursor_pos = 0

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if cursor_pos > 0:
                command = command[:cursor_pos - 1] + command[cursor_pos:]
                cursor_pos -= 1

        elif key == 23:
            if cursor_pos > 0:
                left_part = command[:cursor_pos]
                last_space = left_part.rfind(' ') if ' ' in left_part else 0
                command = command[:last_space] + command[cursor_pos:]
                cursor_pos = last_space

        elif key == curses.KEY_LEFT and cursor_pos > 0:
            cursor_pos -= 1
        elif key == curses.KEY_RIGHT and cursor_pos < len(command):
            cursor_pos += 1
        elif key == curses.KEY_HOME:
            cursor_pos = 0
        elif key == curses.KEY_END:
            cursor_pos = len(command)
        elif key == curses.KEY_UP and history_index < len(command_history) - 1:
            history_index += 1
            command = command_history[-1 - history_index]
            cursor_pos = len(command)
        elif key == curses.KEY_DOWN:
            if history_index > -1:
                history_index -= 1
                command = "" if history_index == -1 else command_history[-1 - history_index]
                cursor_pos = len(command)
        elif 32 <= key <= 126:
            command = command[:cursor_pos] + chr(key) + command[cursor_pos:]
            cursor_pos += 1

    open_powershell_with_cd(os.getcwd())

if __name__ == "__main__":
    curses.wrapper(main)