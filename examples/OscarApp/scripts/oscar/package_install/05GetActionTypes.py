# Set creds and headers
pc_user = "@@{pc_creds.username}@@"
pc_pass = "@@{pc_creds.secret}@@"
headers = {"Content-Type": "application/json", "Accept": "application/json"}


# Set the url and payload
url = "https://localhost:9440/api/nutanix/v3/action_types/list"
payload = {"length": 100}

# Make the request
resp = urlreq(
    url,
    verb="POST",
    auth="BASIC",
    user=pc_user,
    passwd=pc_pass,
    params=json.dumps(payload),
    headers=headers,
    verify=False,
)

# If the request went through correctly
if resp.ok:

    # Create dictionary based on response content body
    entities = json.loads(resp.content)["entities"]

    # Loop through the entities, find matching 'name's, print(out UUID
    for entity in entities:
        if entity["status"]["resources"]["name"] == "vm_add_memory_action":
            print("ACTION_VMAMA_UUID=" + entity["metadata"]["uuid"])
        elif entity["status"]["resources"]["name"] == "resolve_alert":
            print("ACTION_RA_UUID=" + entity["metadata"]["uuid"])
        elif entity["status"]["resources"]["name"] == "email_action":
            print("ACTION_EA_UUID=" + entity["metadata"]["uuid"])

# In case the request returns an error
else:
    print("Post action_types list request failed", resp.content)
    exit(1)
