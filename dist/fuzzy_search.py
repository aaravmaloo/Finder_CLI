import os
import curses
import platform


home_dir = os.path.expanduser("~")
finder_cli_dir = os.path.join(home_dir, "finder_cli")
index_file = os.path.join(finder_cli_dir, "index.txt")

def main(stdscr):

    if not os.path.exists(index_file):
        stdscr.addstr(1, 2, "No index found. Run indexer.py first.")
        stdscr.refresh()
        stdscr.getch()
        return

    with open(index_file, "r", encoding="utf-8") as f:
        full_paths = f.read().splitlines()
    items = [(os.path.basename(path), path) for path in full_paths]

    if not items:
        stdscr.addstr(1, 2, "Index is empty. Run indexer.py again.")
        stdscr.refresh()
        stdscr.getch()
        return


    curses.curs_set(1)
    query = ""
    selected_idx = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        max_display = height - 2


        if query:
            filtered = [(name, path) for name, path in items if query.lower() in name.lower()]
        else:
            filtered = items


        if not filtered:
            selected_idx = 0
        else:
            selected_idx = max(0, min(selected_idx, len(filtered) - 1))


        for i, (name, _) in enumerate(filtered[:max_display]):
            display_name = name[:width - 1]
            if i == selected_idx:
                stdscr.addstr(i, 0, display_name, curses.A_REVERSE)
            else:
                stdscr.addstr(i, 0, display_name)


        prompt = f"Find> {query}"
        stdscr.addstr(height - 1, 0, prompt[:width - 1])
        stdscr.move(height - 1, min(len(prompt), width - 1))
        stdscr.refresh()


        key = stdscr.getch()
        if key == 27:
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
                    stdscr.addstr(height - 2, 0, f"Error: {str(e)}"[:width - 1])
                    stdscr.refresh()
                    stdscr.getch()


        if key == 27:
            stdscr.nodelay(True)
            next_key = stdscr.getch()
            if next_key == 91:
                arrow_key = stdscr.getch()
                if arrow_key == 65:
                    selected_idx = max(0, selected_idx - 1)
                elif arrow_key == 66:
                    if filtered:
                        selected_idx = min(len(filtered) - 1, selected_idx + 1)
            stdscr.nodelay(False)

if __name__ == "__main__":
    curses.wrapper(main)