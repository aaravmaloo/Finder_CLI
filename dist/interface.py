from pip._internal.utils.misc import format_size
from rich.tree import Tree
from rich.console import Console
import os






def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

def list_dir(path="."):
        tree = Tree(f"{path}")

        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                tree.add(f"{item}")  # Folder
            else:
                size = os.path.getsize(full_path)
                tree.add(f" {item} {format_size(size)})")

        console = Console()
        console.print(tree)





class ui:
    def interface(self):
        input_cmd = input(os.getcwd() + "> ")
        working_dir = os.getcwd()
        change_dir = None
        # os.chdir()

        if input_cmd == "cd..":
            os.chdir("..")






        if input_cmd == "dir":
                list_dir()



        if input_cmd == "tutor":
                print("Welcome To Tutorial of Finder_CLI \n")
                print("Finder_CLI is a command line based file explorer, thought and made for programmers. \n")
                print("To be more productive, keyboard is the choice, and a keyboard based full finder is not there; yet. \n")
                print("Meet Finder_CLI, the best cli finder you can get. \n")
                print('Welcome, to use Finder_CLI at its utmost efficiency, you must learn some basic commands, and some advanced commands')
                print('When it shows you the path, it expects you to do something about it... \n')
                print('For this, you need to learn basic cd, dir, find, cd.., move, move_dir, rem_dir, rem... and much more, but for right now, this is basics.')
                print("We'll start with normal commands. ")
                print("you already know what cd, dir does...")



ui_obj = ui()


if __name__ in "__main__":
    while True:
        ui_obj.interface()








