import logging
import os
import string
import sys
from random import choices
from socket import AF_INET, SOCK_STREAM, error, socket
from uuid import uuid4

from pydantic import FilePath


def script_dir(*paths):
    """
    Return the directory of the current script.

    Returns:
        str: The directory of the current script.
    """
    root = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.abspath(".")
    return os.path.join(root, *paths)


def image_path(icon_color):
    """
    Return the path to the icon image based on the provided color.

    Args:
        icon_color (str): The color of the icon.

    Returns:
        str: The full path to the icon image.

    Logs:
        DEBUG: When generating the image path.
        ERROR: If the generated icon path does not exist.
    """
    logging.debug(f"Generating image path for color: {icon_color}")

    # Construct the icon path
    icon_path = script_dir("resources", f"{icon_color}_icon.ico")
    logging.debug(f"Icon path generated: {icon_path}")

    # Log an error if the icon path does not exist
    if not os.path.exists(icon_path):
        logging.error(f"Icon path does not exist: {icon_path}")

    return icon_path


def random_token():
    """
    Generate a random token consisting of alphanumeric characters and a unique ID.

    Returns:
        str: A random token string.

    Logs:
        DEBUG: When generating the random token.
    """
    logging.debug("Generating a random token.")

    # Generate 20 random alphanumeric characters
    random_chars = "".join(choices(string.ascii_letters + string.digits, k=20))
    logging.debug(f"Random alphanumeric characters generated: {random_chars}")

    # Generate a random unique ID
    unique_id = str(uuid4())
    logging.debug(f"Unique ID generated: {unique_id}")

    return f"{random_chars}{unique_id}"


def file_content(file_path:FilePath):
    """
    Read the content of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.

    Logs:
        DEBUG: When reading the file content.
        ERROR: If the file cannot be read.
    """
    logging.debug(f"Reading file content from: {file_path}")
    try:
        with open(file_path, "r") as file:
            content = file.read()
        logging.debug("File content successfully read.")
        return content
    except Exception as e:
        logging.error(f"Failed to read file content: {e}")
        raise


def is_port_in_use(port):
    """
    Check if the given port is in use on the local machine.

    Args:
        port (int): The port number to check.

    Returns:
        bool: True if the port is in use, False otherwise.

    Logs:
        DEBUG: When checking the port status.
    """
    logging.debug(f"Checking if port {port} is in use.")
    with socket(AF_INET, SOCK_STREAM) as s:
        try:
            # Attempt to bind the socket to the specified port
            s.bind(("127.0.0.1", port))
            logging.debug(f"Port {port} is not in use.")
            return False
        except error:
            # If binding fails, it means the port is in use
            logging.debug(f"Port {port} is in use.")
            return True
