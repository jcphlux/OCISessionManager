import logging
from tkinter import Tk

import sv_ttk

from ui.app import App

if __name__ == "__main__":
    logging.info("Starting OCI Bastion Connector...")
    root = Tk()
    sv_ttk.use_light_theme()

    app = App(root)
    app.pack(expand=True, fill="both")

    root.mainloop()

