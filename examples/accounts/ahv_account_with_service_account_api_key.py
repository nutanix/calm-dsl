"""
Nutanix AHV Account Example - Service Account API Key Authentication

This example demonstrates how to create a Nutanix AHV account using
service account API key authentication (available in Calm 4.3.0+).

Prerequisites:
1. Create a service account in Prism Central with an API key
2. Create an authorization policy with NCM Connector or Super Admin role
3. Assign the service account to the authorization policy

For more information, refer to:
- https://portal.nutanix.com/page/documents/details?targetId=Nutanix-Security-Guide-v7_3:mul-service-account-configure-pc-t.html
- https://portal.nutanix.com/page/documents/details?targetId=Nutanix-Security-Guide-v7_3:mul-authorization-policy-configure-iam-pc-t.html
"""

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT


class NutanixServiceAccountExample(Account):
    """
    Nutanix AHV Account with Service Account API Key Authentication
    """

    type = ACCOUNT.TYPE.AHV
    sync_interval = 3600  # Sync interval in seconds

    resources = AccountResources.Ntnx(
        server="10.20.30.40",  # Prism Central IP address
        port="9440",  # Prism Central port
        service_account_api_key="your-service-account-api-key-here",  # Service account API key
    )

