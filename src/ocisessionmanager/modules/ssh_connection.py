import logging
import subprocess
import threading
import time
from ocisessionmanager.modules.config import config


class SSHConnection:
    """Class to handle SSH connections via subprocess."""

    def __init__(self):
        self._connected = False
        self._callbacks = []
        self._process = None
        self._retry_count = 0
        self._max_retries = config.settings.connectionmaxretries
        self._check_interval = config.settings.checkconnectioninterval
        self._should_reconnect = True
        logging.debug("SSHConnection initialized with subprocess.")
    @property
    def state(self):
        return self._connected

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        if self._connected == value:
            return
        self._connected = value
        state = "established" if value else "lost"
        logging.info(f"SSH connection {state}.")
        self._notify_callbacks()

    def connect(self):
        """Establishes SSH connection using subprocess."""
        logging.info("Attempting to connect using subprocess SSH.")
        self._should_reconnect = True

        bastion_host = config.connectionsettings.bastionhost
        bastion_port = config.connectionsettings.bastionport
        target_ip = config.connectionsettings.targetip
        target_port = config.connectionsettings.targetport
        local_port = config.connectionsettings.localport
        session_ocid = config.connectionsettings.sessionocid
        priv_key_path = config.keypaths.privkeypath

        ssh_command = [
            "ssh",
            "-i", priv_key_path,
            "-N",
            "-L", f"{local_port}:{target_ip}:{target_port}",
            "-p", str(bastion_port),
            f"{session_ocid}@{bastion_host}"
        ]

        logging.debug(f"SSH command: {' '.join(ssh_command)}")

        def run_ssh():
            while self._should_reconnect and self._retry_count <= self._max_retries:
                error_message: str = ""
                try:
                    self._process = subprocess.Popen(
                        ssh_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )

                    stdout, stderr = self._process.communicate()
                    if stderr:
                        error_message = stderr.decode().strip()
                        logging.error(error_message)
                    else:
                        self.connected = True
                        self._retry_count = 0
                except Exception as e:
                    logging.error(f"Error during SSH subprocess: {e}")
                finally:
                    self.connected = False
                    if (
                        not self._should_reconnect
                        or "Permission denied" in error_message
                    ):
                        self._retry_count = 0
                        break
                    self._retry_count += 1
                    if self._retry_count > self._max_retries:
                        logging.error("Max reconnect attempts reached, not trying again.")
                        break
                    logging.info(f"Connection lost. Retrying in {self._check_interval} seconds (Attempt {self._retry_count}/{self._max_retries})")
                    time.sleep(self._check_interval)

        threading.Thread(target=run_ssh, daemon=True).start()

    def disconnect(self):
        """Closes the SSH subprocess connection."""
        logging.info("Disconnecting subprocess SSH...")
        self._should_reconnect = False
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process.wait()
            logging.info("SSH subprocess terminated.")
        self.connected = False

    def toggle(self):
        """Toggles the SSH connection state."""
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def register_connection_callback(self, callback):
        """Adds a callback function to be called when the connection status changes."""
        self._callbacks.append(callback)
        logging.debug("Callback added for connection status changes.")

    def _notify_callbacks(self):
        """Notifies all registered callbacks of connection status changes."""
        logging.debug("Notifying callbacks of connection status change.")
        for callback in self._callbacks:
            callback(self._connected)
