import base64
import json
import logging
import subprocess
import threading
from datetime import datetime, timedelta, timezone
from typing import Callable

from oci import config as oci_config
from oci.auth.signers import SecurityTokenSigner
from oci.exceptions import ConfigFileNotFound, ProfileNotFound
from oci.identity import IdentityClient
from oci.signer import load_private_key_from_file


class OCISessionManager:
    def __init__(
        self,
        profile_name: str,
        region: str,
        config_file: str = oci_config.DEFAULT_LOCATION,
        config_overrides: dict = None,
    ):
        """
        Initializes the OCISessionManager with OCI CLI profile information.

        Args:
            profile_name (str): Name of the OCI CLI profile.
            region (str): OCI region.
            config_file (str, optional): Path to the OCI config file. Defaults to OCI default location.
            config_overrides (dict, optional): Overrides for the OCI configuration.
        """
        logging.debug("Initializing OCISessionManager...")
        if not self.cli_installed():
            raise EnvironmentError("OCI CLI is not installed or accessible.")

        self._profile_name = profile_name
        self._region = region
        self._config_file = config_file
        self._config_overrides = config_overrides or {}
        self._config = {}
        self._security_token = None
        self._timer = None
        self._callbacks = []
        self._auto_renew = False

        self._load_profile()

    @staticmethod
    def cli_installed():
        """
        Check if OCI CLI is installed.

        Returns:
            bool: True if OCI CLI is installed, False otherwise.
        """
        try:
            result = subprocess.run(
                ["oci", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                logging.info(f"OCI CLI version: {result.stdout.strip()}")
                return True
            return False
        except FileNotFoundError:
            logging.error("OCI CLI not found.")
            return False

    def _load_profile(self):
        """
        Loads OCI CLI profile configuration.

        Raises:
            ConfigFileNotFound: If the config file is not found.
            ProfileNotFound: If the profile is not found in the config file.
        """
        logging.debug(f"Loading profile '{self._profile_name}' from config file...")
        try:
            self._config = oci_config.from_file(
                file_location=self._config_file, profile_name=self._profile_name
            )
            self._load_security_token()
            logging.info(f"Profile '{self._profile_name}' loaded successfully.")
        except (ConfigFileNotFound, ProfileNotFound) as e:
            logging.error(f"Error loading profile: {e}")

    def _load_security_token(self):
        """
        Loads the security token from the configured file.

        Raises:
            ValueError: If the security token file is missing in the config.
        """
        logging.debug("Loading security token...")
        try:
            token_file = self.config.security_token_file")
            if token_file:
                with open(token_file, "r") as file:
                    self._security_token = file.read().strip()
                logging.info("Security token loaded successfully.")
            else:
                raise ValueError("security_token_file missing in config")
        except Exception as e:
            logging.error(f"Error loading security token: {e}")
            self._security_token = None

    @property
    def config(self):
        """
        Returns the OCI CLI configuration with overrides applied.

        Returns:
            dict: The merged configuration.
        """
        config = self._config.copy()
        config.update(self._config_overrides)
        return config

    @property
    def profile_name(self):
        return self._profile_name

    @property
    def region(self):
        return self.config.region") if self._config else None

    @property
    def key_file(self):
        return self._config.key_file") if self._config else None

    @property
    def root_tenancy(self):
        return self._config.tenancy") if self._config else None

    @property
    def tenancy(self):
        return self.config.tenancy") if self._config else None

    @property
    def expired(self):
        """Checks if the current security token is expired."""
        try:
            return self._get_token_expiration_delay() == 0
        except Exception as e:
            logging.error(f"Error checking token expiration: {e}")
            return True

    @property
    def private_key(self):
        """Returns the private key from the key file."""
        return load_private_key_from_file(self.key_file)

    @property
    def signer(self):
        """Returns the security token signer."""
        return SecurityTokenSigner(self._security_token, self.private_key)

    @property
    def identity(self):
        """Returns the identity client."""
        return IdentityClient(self._config, signer=self.signer)

    def _renew_security_token(self, force_new=False):
        """
        Renews or authenticates a new security token.

        Args:
            force_new (bool): Whether to force a new authentication.

        Returns:
            bool: True if the token was renewed successfully, False otherwise.
        """
        cmd = [
            "oci",
            "session",
            "authenticate" if force_new else "refresh",
            "--profile-name" if force_new else "--profile",
            self.profile_name,
        ]
        if force_new:
            cmd += ["--auth", "security_token", "--region", self._region]

        logging.info(f"Executing OCI CLI command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            self._load_security_token()
            logging.info("Token renewed successfully.")
            return True

        logging.error(f"Token renewal failed: {result.stderr}")
        return False

    def _get_token_expiration_delay(self):
        """
        Calculates time remaining until the token expires.

        Returns:
            int: Time in seconds until the token expires. Returns 0 if expired.
        """
        if not self._security_token:
            logging.warning("No security token available.")
            return 0

        try:
            payload = base64.urlsafe_b64decode(
                self._security_token.split(".")[1] + "=="
            ).decode()
            exp_time = json.loads(payload).get("exp")
            expiration_delay = (
                datetime.fromtimestamp(exp_time, timezone.utc)
                - datetime.now(timezone.utc)
            ).total_seconds()
            return max(expiration_delay, 0)
        except Exception as e:
            logging.error(f"Error decoding token expiration: {e}")
            return 0

    def _schedule_token_renewal(self):
        """
        Schedules token renewal before expiration.
        """
        delay = max(self._get_token_expiration_delay() - 120, 0)
        self._timer = threading.Timer(delay, self._renew_token)
        self._timer.start()
        logging.info(f"Token renewal scheduled in {delay} seconds.")

    def _renew_token(self, force_new=False):
        """
        Renews token and schedules next renewal if successful.

        Args:
            force_new (bool): Whether to force a new authentication.
        """
        logging.debug("Renewing token...")
        if self._auto_renew:
            success = self._renew_security_token(force_new)
            if success:
                self._schedule_token_renewal()
            expiration_time = datetime.now() + timedelta(
                seconds=self._get_token_expiration_delay()
            )
            self._notify_callbacks(success, expiration_time)

    def start(self):
        """
        Starts automatic token renewal management.
        """
        logging.info("Starting OCISessionManager...")
        self._auto_renew = True
        success = True
        if self.expired:
            success = self._renew_security_token(force_new=True)
        else:
            self._schedule_token_renewal()
        expiration_time = datetime.now() + timedelta(
            seconds=self._get_token_expiration_delay()
        )
        self._notify_callbacks(success, expiration_time)

    def stop(self):
        """
        Stops automatic token renewal management.
        """
        logging.info("Stopping OCISessionManager...")
        self._auto_renew = False
        if self._timer:
            self._timer.cancel()

    def add_callback(self, callback: Callable[[bool, datetime], None]):
        """
        Registers a callback function to be called upon token status changes.

        Args:
            callback (Callable[[bool, datetime], None]): The callback function.
        """
        logging.debug("Adding callback...")
        self._callbacks.append(callback)

    def _notify_callbacks(self, success: bool, expiration_time: datetime):
        """
        Notifies registered callbacks of token renewal status and expiration time.

        Args:
            success (bool): Whether the token renewal was successful.
            expiration_time (datetime): The new token expiration time.
        """
        logging.debug("Notifying callbacks...")
        local_expiration_time = expiration_time.astimezone()
        for callback in self._callbacks:
            callback(success, local_expiration_time)


# # Example usage
# if __name__ == "__main__":
#     # Configure logger
#     logging.basicConfig(level=logging.DEBUG)

#     # Print all region names and identifiers
#     for region_name in REGIONS:
#         print(region_name)

#     # Initialize and start the OCISessionManager
#     logging.info("Initializing OCISessionManager...")
#     token_manager = OCISessionManager("OC2_Test", "us-luke-1")

#     def notify(success: bool, expiration_time: datetime):

#         formatted_time = expiration_time.strftime("%Y-%m-%d %H:%M:%S")
#         logging.info(f"Token expiration time: {formatted_time}")
#         if success:
#             logging.info("Token renewal successful from callback.")
#         else:
#             logging.info("Token renewal failed from callback.")

#     token_manager.add_callback(notify)

#     token_manager.start()

#     # # Continue with the rest of your code
#     # logging.info("Loading OCI private key...")
#     # oci_private_key = oci.signer.load_private_key_from_file(token_manager.key_file)
#     # oci_security_token_signer = oci.auth.signers.SecurityTokenSigner(
#     #     token_manager._security_token, oci_private_key
#     # )

#     # logging.info("Creating OCI IdentityClient...")
#     # identity = oci.identity.IdentityClient(
#     #     token_manager.config, signer=oci_security_token_signer
#     # )

#     # logging.info("Listing all regions...")
#     # print(identity.list_regions().data)  # List all regions

#     # logging.info("Listing all compartments...")
#     # print(
#     #     identity.list_compartments(token_manager.tenancy).data
#     # )  # List all compartments

#     # logging.info("Listing all users...")
#     # print(identity.list_users(token_manager.tenancy).data)  # List all users

#     # logging.info("Listing all groups...")
#     # print(identity.list_groups(token_manager.tenancy).data)  # List all groups

#     # add loop to keep the program running for testing

#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         logging.info("Program interrupted by user.")

#     # Stop the token manager when the program ends
#     logging.info("Stopping OCISessionManager before program exit...")
#     token_manager.stop()
