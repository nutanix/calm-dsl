# Set creds and headers
pc_user = "@@{pc_creds.username}@@"
pc_pass = "@@{pc_creds.secret}@@"
headers = {"Content-Type": "application/json", "Accept": "application/json"}

# Set the url and payload
url = "https://localhost:9440/api/nutanix/v3/action_rules/@@{PLAYBOOK_UUID}@@"

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
    print("Playbook deleted successfully:")
    print(json.dumps(json.loads(resp.content), indent=4))
    exit(0)

# In case the request returns an error
else:
    print("Playbook Delete request failed:")
    print(json.dumps(json.loads(resp.content), indent=4))
    exit(1)
