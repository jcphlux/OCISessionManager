import json
import logging
from logging.handlers import TimedRotatingFileHandler
from math import e
import os
from pathlib import Path
import platform
from re import A, L
import sys
import threading
from platformdirs import user_config_dir, user_log_dir, user_log_path

from ocisessionmanager.models import ConfigModel
from ocisessionmanager.modules.simple_logging_handler import SimpleLoggingHandler


def _config_json() -> str:
    """Returns the config as a JSON string."""
    global config
    return config.model_dump(mode="json")


def _load_config():
    """Loads the config from the file if it exists, otherwise creates a default one."""
    global config, _config_path
    if not os.path.exists(_config_path):
        config = ConfigModel()
        with open(_config_path, "w") as configfile:
            json.dump(_config_json(), configfile, indent=4)
        logging.info(f"Created default config at {_config_path}")
    else:
        with open(_config_path, "r") as configfile:
            config = ConfigModel(**json.load(configfile))
        logging.debug(f"Loaded config from {_config_path}")

    # Set up a callback to save the config when it changes
    config.subscribe(_debounce_save_config)


def _save_config():
    """Saves the current config values to the file."""
    global _save_timer, _config_path, config
    # Cancel the timer if it exists
    if _save_timer:
        _save_timer.cancel()
        _save_timer = None

    try:
        # Save the config to the file from the config model
        with open(_config_path, "w") as configfile:
            json.dump(_config_json(), configfile, indent=4)
        config.reset_changes()  # Reset changes after saving
        logging.debug(f"Saved config to {_config_path}")
    except Exception as e:
        logging.error(f"Error saving config: {e}")


def _debounce_save_config(name: str, value):
    """Debounce the config save operation to avoid frequent writes."""
    global _save_timer, config
    if _save_timer:
        _save_timer.cancel()
    _save_timer = threading.Timer(
        config.settings.autosavedebounceinterval, _save_config
    )
    _save_timer.start()


# Define persistent config path
APP_NAME = "OCI Session Manager"
AUTHOR = "PhluxApps"  # Optional, for Windows/Mac
APP_DIR = config_path = Path(user_config_dir(APP_NAME, AUTHOR), ensure_exists=True)  # Use platformdirs to get the user config directory

config: ConfigModel
_config_path = APP_DIR / "config.json"
_save_timer = None  # Timer for debounce functionality

# Setup logging
log_data = SimpleLoggingHandler()

log_dir = Path(user_log_dir(APP_NAME, AUTHOR, ensure_exists=True))  # Directory for logs
log_file_name = f"{APP_NAME.replace(' ', '_').lower()}_log.log"
log_file_path = log_dir / log_file_name
timed_file_handler = TimedRotatingFileHandler(
    log_file_path, when="midnight", interval=1, backupCount=14
)

# Create a custom formatter
log_format = "%(asctime)s - %(levelname)s - %(message)s - %(name)s - %(filename)s:%(lineno)d - %(exc_text)s"
formatter = logging.Formatter(log_format)
timed_file_handler.setFormatter(formatter)

logging.basicConfig(
    handlers=[timed_file_handler, log_data],
    level=logging.DEBUG,
)


# Load or create the config
_load_config()
