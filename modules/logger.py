import logging
import os
from collections import deque
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler


class SimpleLoggingHandler(logging.Handler):
    """Custom logging handler that writes log records to a deque (for timestamps) and a list (for formatted data)."""

    _log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    _timestamps = deque()  # Use deque to store raw timestamps
    _log_data = []  # List to store formatted log entries
    _filtered_log_data = []  # List to store filtered log entries
    _log_level = "DEBUG"  # Default log level
    _update_log_callbacks = []

    def __init__(self):
        super().__init__()

    def emit(self, record):
        """Handle a new log record."""
        # Get the raw timestamp
        timestamp = datetime.fromtimestamp(record.created)

        # Format the timestamp as a string for display
        formatted_time = timestamp.strftime("%I:%M:%S %p")

        # Other log data
        level = record.levelname
        msg = record.message
        stack_trace = record.exc_text if record.exc_info else ""

        # Remove records older than 3 hours
        self._remove_old_records()

        # Store the raw timestamp in the deque
        self._timestamps.append(timestamp)

        # Store the formatted log entry (for display purposes)
        self._log_data.append((formatted_time, level, msg, stack_trace))

        # Update the log display based on the selected log level
        self.filter_log_entries(self._log_level)

    def filter_log_entries(self, log_level):
        """Return the filtered log entries based on the selected log level."""
        self._log_level = log_level
        if log_level == "DEBUG":
            self._filtered_log_data = self._log_data.copy()  # Display all logs
        else:
            level_index = self._log_levels.index(log_level)
            self._filtered_log_data = [
                entry
                for entry in self._log_data
                if any(level in entry for level in self._log_levels[level_index:])
            ]

        # Notify any filtered callbacks (display filtered log entries)
        self._notify_update_callbacks()

    def _remove_old_records(self):
        """Remove records older than 3 hours from the deque and the log data list."""
        current_time = datetime.now()

        # Remove old timestamps and corresponding log data
        valid_indices = [
            i
            for i, timestamp in enumerate(self._timestamps)
            if current_time - timestamp <= timedelta(hours=3)
        ]

        # Keep the valid logs in both collections (timestamps and formatted data)
        self._timestamps = [self._timestamps[i] for i in valid_indices]
        self._log_data = [self._log_data[i] for i in valid_indices]

    def _notify_update_callbacks(self):
        """Notify all registered callbacks to update the log display."""
        for callback in self._update_log_callbacks:
            filtered_log_data = self._filtered_log_data.copy()
            callback(filtered_log_data)

    def register_update_callback(self, callback):
        """Register a callback for filtered log entries."""
        self._update_log_callbacks.append(callback)


log_data = SimpleLoggingHandler()


def initialize_logging(app_dir):

    # Ensure the log directory exists
    log_dir = os.path.join(app_dir, "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_path = os.path.join(log_dir, "oci_bastion_connector.log")
    timed_file_handler = TimedRotatingFileHandler(
        log_file_path, when="midnight", interval=1, backupCount=14
    )

    # Create a custom formatter
    log_format = (
        "%(asctime)s - %(levelname)s - %(message)s - %(name)s - %(filename)s:%(lineno)d - %(exc_text)s"
    )
    formatter = logging.Formatter(log_format)
    timed_file_handler.setFormatter(formatter)

    logging.basicConfig(
        handlers=[timed_file_handler, log_data],
        level=logging.DEBUG,
    )
