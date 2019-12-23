# Set creds and headers
pc_user = "@@{pc_creds.username}@@"
pc_pass = "@@{pc_creds.secret}@@"
headers = {"Content-Type": "application/json", "Accept": "application/json"}

# Set the url and payload
url = "https://localhost:9440/PrismGateway/services/rest/v2.0/alerts/policies/@@{ALERT_UUID}@@"

# Make the request
resp = urlreq(
    url,
    verb="DELETE",
    auth="BASIC",
    user=pc_user,
    passwd=pc_pass,
    headers=headers,
    verify=False,
)

# If the request went through correctly
if resp.ok:
    print("Alert deleted successfully:")
    exit(0)

# In case the request returns an error
else:
    print("Alert Delete request failed:")
    print(json.dumps(json.loads(resp.content), indent=4))
    exit(1)
