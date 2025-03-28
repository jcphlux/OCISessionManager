import logging
from tkinter import messagebox
from tkinter.ttk import Frame, Treeview

from ocisessionmanager.interfaces.app import IApp
from ocisessionmanager.interfaces.logging_tab import ILoggingTab
from ocisessionmanager.modules.config import log_data
from ocisessionmanager.ui.widgets import EnumComboBoxField, SwitchButton


class LoggingTab(ILoggingTab, Frame):
    """Class to handle the logging tab in the UI."""

    _app: IApp

    def __init__(self, app: IApp):
        """
        Initialize the logging tab.

        Args:
            app (IApp): The main application instance.
        """
        Frame.__init__(self, app.notebook)
        self._app = app
        self.create_ui()

    def create_ui(self):
        """Create the UI elements for the connection tab."""

        logging.debug("Initializing connection tab UI components")
        self._app.notebook.add(self, text="Logging")

        self.autoscroll_checkbox = SwitchButton(self, "settings.autoscrolllog", False)
        self.autoscroll_checkbox.grid(row=0, column=2, padx=10, pady=10)
        self.log_level_ddl = EnumComboBoxField(self, "settings.displayloglevel", False)
        self.log_level_ddl.grid(row=0, column=3, padx=10, pady=10)
        self.log_level_ddl.widget.bind("<<ComboboxSelected>>", self.on_log_level_change)

        columns = ["Time", "Level", "Log Message", "Stack"]
        self.log_tree = Treeview(self, columns=columns, show="headings")
        self.log_tree.heading("Time", text="Time")
        self.log_tree.column("Time", width=50, stretch=False)
        self.log_tree.heading("Level", text="Level")
        self.log_tree.column("Level", width=60, stretch=False)
        self.log_tree.heading("Log Message", text="Log Message")
        self.log_tree.column("Log Message", width=400, stretch=True)
        self.log_tree.heading("Stack", text="Stack")
        self.log_tree.column("Stack", width=50, stretch=False)
        self.log_tree.grid(
            row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew"
        )
        self.log_tree.bind("<Double-1>", self.show_stack_trace)
        logging.debug("Created and configured log Treeview.")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        logging.debug("Configured grid layout for connection frame.")

        log_data.register_update_callback(
            lambda log_data: self._app.root.after(0, self.on_data_update, log_data)
        )
        logging.debug("Registered callbacks for connection change and log data update.")

        # Start the log updating process
        selected_log_level = self.log_level_ddl.value
        log_data.filter_log_entries(selected_log_level)
        logging.debug(f"Initial log level set to: {selected_log_level}")

    def on_data_update(self, log_data: list):
        """Update the log text in the Treeview based on the current log level filter."""
        if self._app.visible:
            self.log_tree.delete(*self.log_tree.get_children())
            for entry in log_data:
                formatted_time, level, msg, stack_trace = entry
                view_text = "View" if stack_trace.strip() else " "
                self.log_tree.insert(
                    "", "end", values=(formatted_time, level, msg, view_text)
                )
            if self.autoscroll_checkbox.value:
                self.log_tree.yview_moveto(1)

    def on_log_level_change(self, event):
        """Update the display based on the selected log level."""
        selected_log_level = self.log_level_ddl.value

        log_data.filter_log_entries(selected_log_level)
        logging.info(f"Log level filter applied: {selected_log_level}")

    def show_stack_trace(self, event):
        """Show the stack trace in a message box."""
        selected_item = self.log_tree.selection()[0]
        stack_trace = log_data.loc[self.log_tree.index(selected_item), "Stack"]
        logging.debug(
            f"Showing stack trace for log entry: {self.log_tree.index(selected_item)}"
        )
        if stack_trace.strip():
            messagebox.showinfo("Stack Trace", stack_trace)
            logging.info("Displayed stack trace in message box.")
