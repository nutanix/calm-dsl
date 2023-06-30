import json
import os

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT

PROJECT_ID = "project_id_updated"
PRIVATE_KEY_ID = "private_key_id_updated"
PRIVATE_KEY = "private_key_updated"
CLIENT_EMAIL = "example_updated@example.com"
TOKEN_URI = "https://accounts.google.com/o/oauth2/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
AUTH_PROVIDER_x509_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
CLIENT_x509_CERT_URL = "https://www.googleapis.com/robot/v1/metadata/x509/108048128720-compute%40developer.gserviceaccount.com"
CLIENT_ID = "123213123123123"
SERVER_IP = "server_ip_updated"
PORT = 944
PUBLIC_IMAGE_1 = "PUBLIC_IMAGE_1_updated"
PUBLIC_IMAGE_2 = "PUBLIC_IMAGE_2_updated"

SYNC_INTERVAL_SECS = 3900


class test_gcp_updated_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.GCP
    resources = AccountResources.Gcp(
        project_id=PROJECT_ID,
        private_key_id=PRIVATE_KEY_ID,
        private_key=PRIVATE_KEY,
        client_email=CLIENT_EMAIL,
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        auth_uri=AUTH_URI,
        auth_provider_cert_url=AUTH_PROVIDER_x509_CERT_URL,
        client_cert_url=CLIENT_x509_CERT_URL,
        regions=["eu-central-1"],
        public_images=[PUBLIC_IMAGE_1, PUBLIC_IMAGE_2],
        gke_config={"server": SERVER_IP, "port": PORT},
    )
