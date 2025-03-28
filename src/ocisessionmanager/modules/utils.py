import importlib.resources as resources
import logging
from random import choices
from socket import AF_INET, SOCK_STREAM, error, socket
from string import ascii_letters, digits
from subprocess import run
from uuid import uuid4

from pydantic import FilePath

def icon_path(icon_color):
    """
    Return the path to the icon image based on the provided color.

    Args:
        icon_color (str): The color of the icon.

    Returns:
        str: The full path to the icon image.

    Logs:
        DEBUG: When generating the icon path.
        ERROR: If the icon path does not exist.
        ERROR: If the icon path cannot be generated.

    Raises:
        FileNotFoundError: If the icon path does not exist.
    """
    logging.debug(f"Generating image path for color: {icon_color}")

    # Construct the icon path
    try:
        with resources.path(
            "ocisessionmanager.resources", f"{icon_color}_icon.png"
        ) as icon_path:
            logging.debug(f"Icon path generated: {icon_path}")
            if not icon_path.exists():
                raise FileNotFoundError(icon_path)
            return icon_path
    except FileNotFoundError as e:
        logging.error(f"Icon path does not exist: {e}")
        raise
    except Exception as e:
        logging.error(f"Failed to generate icon path: {e}")
        raise


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
    random_chars = "".join(choices(ascii_letters + digits, k=20))
    logging.debug(f"Random alphanumeric characters generated: {random_chars}")

    # Generate a random unique ID
    unique_id = str(uuid4())
    logging.debug(f"Unique ID generated: {unique_id}")

    return f"{random_chars}{unique_id}"


def file_content(file_path: FilePath):
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


def cli_installed():
    """
    Check if OCI CLI is installed.

    Returns:
        bool: True if OCI CLI is installed, False otherwise.
    """
    try:
        result = run(["oci", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"OCI CLI version: {result.stdout.strip()}")
            return True
        return False
    except FileNotFoundError:
        logging.error("OCI CLI not found.")
        return False
