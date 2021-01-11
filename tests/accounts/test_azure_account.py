from calm.dsl.builtins import Account, AzureAccountSpec
from calm.dsl.constants import PROVIDER


class AzureSpec(AzureAccountSpec):

    subscription_id = "azure_subscription_id"
    tenant_id = "azure_tenant_id"
    client_id = "azure_client_id"
    cloud_environment = "PublicCloud"
    client_key = "azure_client_key"


class AzureAccount(Account):

    provider_type = PROVIDER.AZURE
    spec = AzureSpec
