# python3;success

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import SubscriptionClient
creds = ServicePrincipalCredentials(client_id="client_id_a", secret="client_key",tenant="tenant_id")
subscription_client = SubscriptionClient(creds)
locations = subscription_client.subscriptions.list_locations("subscription_id")
locations = [i.name for i in locations]
sleep(5)
print("eastus2" in locations)