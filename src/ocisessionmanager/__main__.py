import sys

MIN_PYTHON = (3, 10)

if sys.version_info < MIN_PYTHON:
    from tkinter import messagebox, Tk

    root = Tk()
    root.withdraw()  # Hide the root window
    messagebox.showerror(
        "Python Version Error",
        f"Your system is running Python {sys.version_info.major}.{sys.version_info.minor}, "
        f"but this app requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or higher.\n\n"
        "Please install a newer version of Python from https://www.python.org/downloads/",
    )
    sys.exit(1)

from ocisessionmanager.app import main

if __name__ == "__main__":
    main()
