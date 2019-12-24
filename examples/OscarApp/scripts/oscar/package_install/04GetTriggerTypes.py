# Set creds and headers
pc_user = '@@{pc_creds.username}@@'
pc_pass = '@@{pc_creds.secret}@@'
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

# Set the url and payload
url = "https://localhost:9440/api/nutanix/v3/action_trigger_types/list"
payload = {"length": 100}

# Make the request
resp = urlreq(url, verb='POST', auth='BASIC', user=pc_user, passwd=pc_pass,
              params=json.dumps(payload), headers=headers, verify=False)

# If the request went through correctly
if resp.ok:

    # Create dictionary based on response content body
    entities = json.loads(resp.content)['entities']

    # Loop through the entities, find matching 'name', print(out UUID
    for entity in entities:
        if entity['status']['resources']['name'] == 'alert_trigger':
            print('ALERT_TRIGGER_UUID=' + entity['metadata']['uuid'])
            exit(0)

# In case the request returns an error
else:
    print("Post action_types list request failed", resp.content
    exit(1)

print("The script shouldn't have gotten to this point.  If you're seeing")
print("this message then the proper alert_trigger was not found.")
