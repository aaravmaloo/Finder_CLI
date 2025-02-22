from colorama import Fore, Style
from rich.tree import Tree
from rich.console import Console
import os
from pathlib import Path
import shutil
import shlex
import msvcrt

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

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
        print(Fore.RED + "Directory not found." + Style.RESET_ALL)
        return
    except PermissionError:
        print(Fore.RED + "Permission denied." + Style.RESET_ALL)
        return

    console = Console()
    console.print(tree)

def rm(args):
    if not args:
        print(Fore.RED + "Error: No filename specified." + Style.RESET_ALL)
    filename = args[0].strip()
    try:
        os.unlink(filename)
    except FileNotFoundError:
        print(Fore.RED + f"file specified in stdin is not found." + Style.RESET_ALL)
    except PermissionError:
        print(Fore.RED + "permission denied by operating system.")
    return

def rmdir(args):
    if not args:
        print(Fore.RED + "Error: No folder name specified." + Style.RESET_ALL)
    filename = args[0].strip()
    try:
        os.rmdir(filename)
    except FileNotFoundError:
        print(Fore.RED + f"folder specified in stdin is not found.")
    except PermissionError:
        print(Fore.RED + "permission denied by operating system.")
    return



def copy_file(args):
    if len(args) < 2:
        print(Fore.RED + "Error: copy command requires source and destination." + Style.RESET_ALL)
        return

    source, destination = args[0].strip(), args[1].strip()
    if not os.path.exists(source):
        print(Fore.RED + f"Error: Source '{source}' does not exist." + Style.RESET_ALL)
        return

    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(source))

    shutil.copy(source, destination)
    print(Fore.GREEN + f"Moved '{source}' to '{destination}'" + Style.RESET_ALL)

def move_file(args):
    if len(args) < 2:
        print(Fore.RED + "Error: move command requires source and destination." + Style.RESET_ALL)
        return

    source, destination = args[0].strip(), args[1].strip()
    if not os.path.exists(source):
        print(Fore.RED + f"Error: Source '{source}' does not exist." + Style.RESET_ALL)
        return

    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(source))

    shutil.move(source, destination)
    print(Fore.GREEN + f"Moved '{source}' to '{destination}'" + Style.RESET_ALL)

def change_directory(args):
    if not args:
        print(Fore.RED + "Error: No directory specified." + Style.RESET_ALL)
        return

    path = args[0].strip().strip('"').strip("'")

    # Handle special shortcuts directly
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
        # For other paths, expand user and make absolute
        full_path = os.path.abspath(os.path.expanduser(path))

    try:
        if not os.path.exists(full_path):
            print(Fore.RED + f"Error: Path '{full_path}' does not exist." + Style.RESET_ALL)
            return
        if not os.path.isdir(full_path):
            print(Fore.RED + f"Error: '{full_path}' is not a directory." + Style.RESET_ALL)
            return

        os.chdir(full_path)
    except FileNotFoundError:
        print(Fore.RED + f"Directory not found: '{path}'" + Style.RESET_ALL)
    except PermissionError:
        print(Fore.RED + f"Permission denied: '{path}'" + Style.RESET_ALL)
    except OSError as e:
        print(Fore.RED + f"Invalid path: {e} (tried '{path}')" + Style.RESET_ALL)

def create_file(args):
    if not args:
        print(Fore.RED + "Error: No filename specified." + Style.RESET_ALL)
        return

    file_name = args[0].strip()
    try:
        Path(file_name).touch()
    except Exception as e:
        print(Fore.RED + f"Error: {e}" + Style.RESET_ALL)

def show_tutorial(_):
    print("Welcome to Finder_CLI tutorial!")
    print("Finder_CLI is a command-line-based file explorer for programmers.")
    print("Basic commands include cd, ls, move, touch, and more.")
    print("Use ~ to refer to your home folder (C:\\Users\\YourName).")

COMMANDS = {
    "ls": lambda _: list_dir(),
    "move": move_file,
    "cd": change_directory,
    "touch": create_file,
    "tutor": show_tutorial,
    "rm": rm,
    "rmdir": rmdir,
    "copy": copy_file,
}

def parse_command():
    while True:

        if msvcrt.kbhit():
            if msvcrt.getch() == b'\x1b':
                return

        raw_command = input(os.getcwd() + "> ").strip()


        if raw_command == "cd..":
            os.chdir("..")
            continue

        try:
            parts = shlex.split(raw_command, posix=False)
        except ValueError:
            print(Fore.RED + "Error: Invalid command syntax (check quotes)." + Style.RESET_ALL)
            continue

        if not parts:
            continue

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Handle shortcuts in a way that avoids concatenation issues
        replacements = {
            "~": os.path.expanduser("~"),
            "*": os.path.join(os.path.expanduser("~"), "Desktop"),
            "!": os.path.join(os.path.expanduser("~"), "Downloads"),
            "&": os.path.join(os.path.expanduser("~"), "AppData"),
            "/": os.path.join(os.path.splitdrive(os.getcwd())[0], os.sep)
        }

        processed_args = []
        for arg in args:
            new_arg = arg
            for shortcut, full_path in replacements.items():
                if shortcut in new_arg:
                    new_arg = new_arg.replace(shortcut, full_path)
            processed_args.append(new_arg)

        if cmd in COMMANDS:
            COMMANDS[cmd](processed_args)
        else:
            print(Fore.RED + "finder_cli command syntax or the command is invalid, please try again" + Style.RESET_ALL)

if __name__ == "__main__":
    try:
        parse_command()
    except KeyboardInterrupt:
        print("\nExiting...")