import json
import os

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT

C2S_ACCOUNT_ADDRESS = "c2s_account_address_updated"
CLIENT_CERTIFICATE = "client_certifcate_updated"
CLIENT_KEY = "client_key_updated"
ROLE = "role_updated"
MISSION = "mission_updated"
AGENCY = "agency_updated"
SYNC_INTERVAL_SECS = 3900


class test_aws_c2s_updated_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.AWS_C2S
    sync_interval = SYNC_INTERVAL_SECS
    resources = AccountResources.Aws_C2s(
        account_address=C2S_ACCOUNT_ADDRESS,
        client_key=CLIENT_KEY,
        client_certificate=CLIENT_CERTIFICATE,
        role=ROLE,
        mission=MISSION,
        agency=AGENCY,
        regions=[{"name": "us-east-1"}],
    )
