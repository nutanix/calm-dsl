# python3;success

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import SubscriptionClient
creds = ClientSecretCredential(client_id="client_id_a", client_secret="client_key",tenant_id="tenant_id_a")
subscription_client = SubscriptionClient(credential=creds)
locations = subscription_client.subscriptions.list_locations("subscription_id")
locations = [i.name for i in locations]
sleep(5)
print("eastus2" in locations)