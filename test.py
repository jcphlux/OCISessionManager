from modules.oci_tools.oci_compute import OCICompute
from modules.oci_tools.oci_session_manager import OCISessionManager

if __name__ == "__main__":

    config_overrides = {
        # "region": "us-gov-ashburn-1",
        "tenancy": "ocid1.tenancy.oc2..aaaaaaaara5nokvjwlgvo2udvxem6psxy7aiqdh5qdl2kla25utbs5yu74eq",
    }
    session_mgr = OCISessionManager(
        "OC2_Test", "us-luke-1", config_overrides=config_overrides
    )
    session_mgr.start()

    # Initialize service client with token manager signer
    compute_client = OCICompute(session_mgr)

    instances = compute_client._retrieve_compute_instances()
    for name,id in compute_client.map:
        print(f"Instance ID: {id}, Display Name: {name}")

    print(f"Total instances: {len(instances)}")
    session_mgr.stop()
