import logging
from tkinter import Tk

import sv_ttk

from ocisessionmanager.modules.utils import cli_installed
from ocisessionmanager.ui.app import App


def main():
    if not cli_installed():
        raise EnvironmentError("OCI CLI is not installed or accessible.")
    logging.info("Starting OCI Bastion Connector...")
    root = Tk()
    sv_ttk.use_light_theme()
    app = App(root)
    app.pack(expand=True, fill="both")
    root.mainloop()
