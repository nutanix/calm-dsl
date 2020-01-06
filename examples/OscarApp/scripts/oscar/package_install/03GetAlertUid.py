# Set creds and headers
pc_user = "@@{pc_creds.username}@@"
pc_pass = "@@{pc_creds.secret}@@"
headers = {"Content-Type": "application/json", "Accept": "application/json"}


# Set the url and payload
url = "https://localhost:9440/api/nutanix/v3/groups"
payload = {
    "entity_type": "alert_check_schema",
    "group_member_attributes": [
        {"attribute": "alert_title"},
        {"attribute": "alert_uid"},
    ],
    "group_member_offset": 0,
    "group_member_count": 100,
    "filter_criteria": "alert_title==@@{Oscar_AHV.name}@@ Memory Constrained Alert",
}

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

    # Print success message and the ALERT_UUID
    print("Post groups alert_uid request successful!")
    for entity in json.loads(resp.content)["group_results"][0]["entity_results"][0][
        "data"
    ]:
        if entity["name"] == "alert_uid":
            print("ALERT_UID=" + entity["values"][0]["values"][0])

# In case the request returns an error
else:
    print("Post groups alert_uid request failed", resp.content)
    exit(1)

print("The script shouldn't have gotten to this point.  If you're seeing")
print("this message then the proper alert_uid was not found.")
