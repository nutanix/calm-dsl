import json

from calm.dsl.builtins import Account, GcpAccountSpec
from calm.dsl.builtins import read_local_file
from calm.dsl.constants import PROVIDER

# Reading data from a local file
GCP_ACCOUNT_SETTINGS = json.loads(read_local_file("gcp_service_account.json"))


class GcpGkeSpec(GcpAccountSpec):

    private_key = GCP_ACCOUNT_SETTINGS["private_key"]
    private_key_id = GCP_ACCOUNT_SETTINGS["private_key_id"]
    token_uri = GCP_ACCOUNT_SETTINGS["token_uri"]
    project_id = GCP_ACCOUNT_SETTINGS["project_id"]
    auth_uri = GCP_ACCOUNT_SETTINGS["auth_uri"]
    auth_provider_x509_cert_url = GCP_ACCOUNT_SETTINGS["auth_provider_x509_cert_url"]
    client_id = GCP_ACCOUNT_SETTINGS["client_id"]
    client_email = GCP_ACCOUNT_SETTINGS["client_email"]
    client_x509_cert_url = GCP_ACCOUNT_SETTINGS["client_x509_cert_url"]
    regions = ["asia-east1", "us-east1"]

    public_images = ["centos-7-v20201216"]
    gke_config = {
        "port": GCP_ACCOUNT_SETTINGS["gke_port"],
        "server": GCP_ACCOUNT_SETTINGS["gke_server"],
    }


class GcpAccount(Account):

    provider_type = PROVIDER.GCP
    spec = GcpGkeSpec
