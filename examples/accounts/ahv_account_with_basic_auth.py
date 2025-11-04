"""
Nutanix AHV Account Example - Basic Authentication

This example demonstrates how to create a Nutanix AHV account using
traditional username/password authentication.

This authentication method is available in all Calm versions.
"""

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT


class NutanixBasicAuthExample(Account):
    """
    Nutanix AHV Account with Basic Authentication (Username/Password)
    """

    type = ACCOUNT.TYPE.AHV
    sync_interval = 3600  # Sync interval in seconds

    resources = AccountResources.Ntnx(
        server="10.20.30.40",  # Prism Central IP address
        port="9440",  # Prism Central port
        username="admin",  # Prism Central username
        password="your-password-here",  # Prism Central password
    )

