import logging
from datetime import datetime, timedelta
from subprocess import PIPE, Popen
from threading import Thread, Timer
from time import sleep
from typing import Callable

from oci.bastion import BastionClient
from oci.bastion.models import (
    CreateManagedSshSessionTargetResourceDetails,
    CreateSessionDetails,
    PublicKeyDetails,
    Session,
    PortForwardingSessionTargetResourceDetails,
)
from oci.exceptions import ServiceError

from ocisessionmanager.modules.config import config
from ocisessionmanager.modules.oci_tools.oci_session_manager import OCISessionManager
from ocisessionmanager.modules.utils import file_content, random_token


class OCIBastionSessions:
    """
    Manages OCI Bastion sessions, including creation, renewal, and callback notifications.

    Attributes:
        bastion_id (str): The OCID of the bastion.
        target_resource_id (str): The OCID of the target resource.
        target_resource_port (int): The port of the target resource.
        session_mgr (OCISessionManager): The session manager for OCI authentication.
        session_ttl_in_seconds (int): Time-to-live for the session in seconds.
    """

    def __init__(
        self,
        bastion_ocid: str,
        target_resource_ocid: str,
        target_resource_port: int,
        local_port: int,
        session_mgr: OCISessionManager,
        session_ttl_in_seconds=10800,
    ):
        """
        Initializes the OCIBastionSessions instance.

        Args:
            bastion_ocid (str): The OCID of the bastion.
            target_resource_ocid (str): The OCID of the target resource.
            target_resource_port (int): The port of the target resource.
            local_port (int): The local port for the SSH connection.
            session_mgr (OCISessionManager): The session manager for OCI authentication.
            session_ttl_in_seconds (int): Time-to-live for the session in seconds.
        """
        # Initialize attributes
        self._auto_renew = False
        self._bastion_ocid = bastion_ocid
        self._callbacks = []
        self._check_interval = (
            config.settings.checkconnectioninterval
        )  # convert to seconds
        self._connected = False
        self._local_port = local_port
        self._max_retries = config.settings.connectionmaxretries
        self._max_sleep_time = 60
        self._process = None
        self._retry_count = 0
        self._session: Session = None
        self._session_mgr = session_mgr
        self._session_ttl_in_seconds = session_ttl_in_seconds
        self._should_reconnect = True
        self._sleep_time = 5
        self._target_resource_ocid = target_resource_ocid
        self._target_resource_port = target_resource_port
        self._timer = None
        self._bastion_client = BastionClient(
            session_mgr.config, signer=session_mgr.signer
        )
        logging.info("OCIBastionSessions initialized.")

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

    def _connect(self):
        """Establishes SSH connection using subprocess."""
        logging.info("Attempting to connect using subprocess SSH.")
        self._should_reconnect = True

        priv_key_path = config.keypaths.privkeypath
        target_details: PortForwardingSessionTargetResourceDetails = self._session.target_resource_details
        target_ip = target_details.target_resource_private_ip_address
        target_port = target_details.target_resource_port
        target = f"{self._local_port}:{target_ip}:{target_port}"
        bastion_host = f"{self._session.id}@{self._session.bastion_id}"

        ssh_command = [
            "ssh",
            "-i",
            priv_key_path,
            "-N",
            "-L",
            target,
            "-p",
            "22",
            bastion_host,
        ]

        logging.debug(f"SSH command: {' '.join(ssh_command)}")

        def _run_ssh():
            while self._should_reconnect and self._retry_count <= self._max_retries:
                error_message: str = ""
                try:
                    self._process = Popen(ssh_command, stdout=PIPE, stderr=PIPE)

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
                        logging.error(
                            "Max reconnect attempts reached, not trying again."
                        )
                        break
                    logging.info(
                        f"Connection lost. Retrying in {self._check_interval} seconds (Attempt {self._retry_count}/{self._max_retries})"
                    )
                    sleep(self._check_interval)

        Thread(target=_run_ssh, daemon=True).start()

    def _disconnect(self):
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
            self._disconnect()
        else:
            self._connect()

    def _schedule_session_renewal(self):
        """
        Schedule the renewal of the bastion session.
        This method sets a timer to renew the session 2 minutes before expiration.
        """
        delay = self._session_ttl_in_seconds - 120  # 2 minutes before expiration
        self._timer = Timer(delay, self._renew_session)
        self._timer.start()
        logging.info(f"Session renewal scheduled in {delay} seconds.")

    def _renew_session(self):
        """
        Renew the bastion session.
        If auto-renew is enabled, a new session is created and callbacks are notified.
        """
        if self._auto_renew:
            logging.info("Attempting to renew bastion session...")
            success = self._generate_bastion_session()
            if success:
                self._schedule_session_renewal()

        self._notify_callbacks()

    def _get_key_details(self):
        """
        Get the public key details from the config file.

        Returns:
            PublicKeyDetails: The public key details object.
        """
        logging.info("Fetching public key details from configuration.")
        public_key_content = file_content(config.keypaths.pubkeypath)
        return PublicKeyDetails(public_key_content)

    def _generate_bastion_session(self):
        """
        Generate a new bastion session.

        Returns:
            bool: True if the session was successfully created, False otherwise.
        """
        try:
            logging.info("Starting bastion session creation process.")
            display_name = f"Session-{datetime.now().strftime('%Y%m%d-%H%M')}"
            opc_retry_token = random_token()
            opc_request_id = random_token()
            success = False

            # Create the bastion session
            response = self._bastion_client.create_session(
                create_session_details=CreateSessionDetails(
                    bastion_id=self._bastion_ocid,
                    target_resource_details=CreateManagedSshSessionTargetResourceDetails(
                        session_type="PORT_FORWARDING",
                        target_resource_id=self._target_resource_ocid,
                        target_resource_port=self._target_resource_port,
                    ),
                    key_details=self._get_key_details(),
                    display_name=display_name,
                    key_type="PUB",
                    session_ttl_in_seconds=self._session_ttl_in_seconds,
                ),
                opc_retry_token=opc_retry_token,
                opc_request_id=opc_request_id,
            )

            if response.status != 202:
                self._session = None
                raise ServiceError("Error creating session")

            self._session = response.data
            logging.info(f"Creating session {self._session.id}...")

            # Wait for the session to become active
            sleep_time = 0
            while (
                self._session.lifecycle_state == "CREATING"
                and sleep_time < self._max_sleep_time
            ):
                logging.info("Session not ready yet, retrying...")
                sleep(self._sleep_time)
                self._session = self._bastion_client.get_session(self._session.id).data
                sleep_time += self._sleep_time

            if self._session.lifecycle_state != "ACTIVE":
                raise ServiceError(
                    f"Session not active: Last state {self._session.lifecycle_state}"
                )

            success = True
            logging.info(f"Session {self._session.id} created successfully.")
        except ServiceError as e:
            logging.error(f"Error creating session: {e}")

        self._auto_renew = success
        return success

    def add_callback(self, callback: Callable[[str, bool, datetime, Session], None]):
        """
        Registers a callback function to be called upon bastion session status change.

        Args:
            callback (Callable[[str, bool, datetime, Session], None]): The callback function.
        """
        logging.info("Adding a new callback.")
        self._callbacks.append(callback)

    def _notify_callbacks(self):
        """
        Notifies registered callbacks of the bastion session status.
        """
        logging.info("Notifying registered callbacks.")
        if self._session is None:
            expiration_time = datetime.now()
        else:
            expiration_time = datetime.strptime(
                self._session.creation_time, "%Y-%m-%dT%H:%M:%S.%fZ"
            ) + timedelta(seconds=self._session_ttl_in_seconds)
        datetime.now() + timedelta(seconds=self._session_ttl_in_seconds)
        local_expiration_time = expiration_time.astimezone()
        state = self._session.lifecycle_state if self._session else "INACTIVE"
        for callback in self._callbacks:
            callback(state, self._connected, local_expiration_time, self._session)
