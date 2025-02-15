import keyboard
import os
import sys



import keyboard

def getin(prompt):
    value = ""  # Stores user input
    print(prompt, end="", flush=True)  # Print prompt without newline

    while True:
        char = keyboard.read_event(suppress=True).name  # Read key event

        if char == "esc":  # Exit on ESC key
            print("\n[Esc pressed] Exiting...")
            return None  # Return None if user cancels

        elif char == "backspace":  # Handle backspace
            value = value[:-1]
            print("\r" + prompt + value + " ", end="", flush=True)  # Update display

        elif char == "enter":  # Confirm input
            print()  # Move to new line
            return value

        elif len(char) == 1:  # Add character to value
            value += char
            print("\r" + prompt + value, end="", flush=True)  # Update display


class ui:
    def __init__(self):
        pass






first_in = input(os.path.realpath(__file__) + "> ")


if first_in.lower() == "tutor":
    print("Welcome To Tutorial of Finder_CLI \n")
    print("Finder_CLI is a command line based file explorer, thought and made for programmers. \n")
    print("To be more productive, keyboard is the choice, and a keyboard based full finder is not there; yet. \n")
    print("Meet Finder_CLI, the best cli finder you can get. \n")
    print('Welcome, to use Finder_CLI at its utmost efficiency, you must learn some basic commands, and some advanced commands')
    print('When it shows you the path, ')

