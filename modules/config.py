import json
import logging
import os
import platform
import sys
import threading

from models.config import ConfigModel
from modules.logger import initialize_logging


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
CONFIG_FILE = "config.json"
config: ConfigModel
_save_timer = None  # Timer for debounce functionality

if hasattr(sys, "_MEIPASS"):
    # Running as an EXE: Store config in platform-specific directories
    if platform.system() == "Windows":
        APP_DIR = os.path.join(os.environ["APPDATA"], APP_NAME)
    else:
        APP_DIR = os.path.join(os.path.expanduser("~/.config"), APP_NAME)
else:
    # Default to current directory for non-EXE runs
    APP_DIR = os.path.abspath(".")

# Ensure the config directory exists
os.makedirs(APP_DIR, exist_ok=True)

# Setup logging
initialize_logging(APP_DIR)

_config_path = os.path.join(APP_DIR, CONFIG_FILE)


# Load or create the config
_load_config()
