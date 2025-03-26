import logging
from types import MappingProxyType

from oci.core import ComputeClient
from oci.core.models import Instance
from oci.pagination import list_call_get_all_results

from modules.oci_tools.oci_session_manager import OCISessionManager


class OCICompute:
    """
    A class to manage and retrieve information about OCI compute instances.

    Attributes:
        _session_mgr (OCISessionManager): The session manager for OCI API interactions.
        _instances (dict): A dictionary of compute instances keyed by their display names.
    """

    def __init__(self, session_mgr: OCISessionManager):
        """
        Initialize the OCICompute instance.

        Args:
            session_mgr (OCISessionManager): The session manager for OCI API interactions.
        """
        self._session_mgr = session_mgr
        self._instances: dict[str, Instance] = {}
        logging.info("Initializing OCICompute and retrieving compute instances.")
        self._retrieve_compute_instances()

    def _retrieve_compute_instances(self):
        """
        Retrieve and store all compute instances in the tenancy.

        This method fetches all compartments in the tenancy, retrieves all compute
        instances in each compartment, and stores them in a dictionary keyed by their
        display names.
        """
        logging.info("Retrieving compute instances from OCI.")
        identity_client = self._session_mgr.identity
        compute_client = ComputeClient(
            self._session_mgr.config, signer=self._session_mgr.signer
        )

        # Get all compartments in the tenancy
        logging.debug("Fetching compartments in the tenancy.")
        compartments = list_call_get_all_results(
            identity_client.list_compartments,
            self._session_mgr.tenancy,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
        ).data

        # Include the root compartment (tenancy itself)
        logging.debug("Adding root compartment to the list.")
        compartments.append(identity_client.get_tenancy(self._session_mgr.tenancy).data)

        # Fetch all instances from all compartments
        instances = []
        for compartment in compartments:
            logging.debug(f"Fetching instances in compartment: {compartment.name}")
            # Uncomment the following line to filter only active compartments
            instances.extend(
                list_call_get_all_results(
                    compute_client.list_instances,
                    compartment.id,
                    lifecycle_state="RUNNING",
                ).data
            )

        # Filter out instances without a display name and store in a dictionary
        self._instances = {
            instance.display_name: instance
            for instance in instances
            if instance.display_name
        }
        logging.info(f"Retrieved {len(self._instances)} compute instances.")

    def refresh(self):
        """
        Refresh the list of compute instances.

        This method re-fetches the compute instances from OCI and updates the internal
        dictionary.
        """
        logging.info("Refreshing compute instances.")
        self._retrieve_compute_instances()

    @property
    def instances(self) -> MappingProxyType[str, Instance]:
        """
        Get a read-only dictionary of compute instances by their display names.

        Returns:
            MappingProxyType: A read-only dictionary of compute instances.
        """
        return MappingProxyType(self._instances)

    @property
    def map(self) -> MappingProxyType[str, str]:
        """
        Get a read-only dictionary mapping instance display names to their IDs.

        Returns:
            MappingProxyType: A read-only dictionary of instance names and IDs.
        """
        return MappingProxyType(
            {
                instance.display_name: instance.id
                for instance in self._instances.values()
            }
        )
