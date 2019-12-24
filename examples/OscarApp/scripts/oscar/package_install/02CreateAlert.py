# Set creds and headers
pc_user = '@@{pc_creds.username}@@'
pc_pass = '@@{pc_creds.secret}@@'
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

# Set the time in microseconds
time_seconds = @@{calm_time("%s")}@@
time_useconds = time_seconds * 1000000

# Set the url and payload
url = "https://localhost:9440/PrismGateway/services/rest/v2.0/alerts/policies"
payload = {
    "auto_resolve": True,
    "created_by": "admin",
    "description": "Alert created by Calm Application @@{calm_application_name}@@",
    "enabled": True,
    "error_on_conflict": False,
    "filter": "entity_type==vm;entity_id==@@{Oscar_AHV.id}@@",
    "impact_types": [
        "Performance"
    ],
    "last_updated_timestamp_in_usecs": time_useconds,
    "policies_to_override": None,
    "related_policies": None,
    "title": "@@{Oscar_AHV.name}@@ Memory Constrained Alert",
    "trigger_conditions": [
        {
            "condition": "vm.memory_usage_ppm=ge=950000",
            "condition_type": "STATIC_THRESHOLD",
            "severity_level": "CRITICAL"
        },
        {
            "condition": "vm.memory_usage_ppm=ge=900000",
            "condition_type": "STATIC_THRESHOLD",
            "severity_level": "WARNING"
        }
    ],
    "trigger_wait_period_in_secs": 0
}

# Make the request
resp = urlreq(url, verb='POST', auth='BASIC', user=pc_user, passwd=pc_pass,
              params=json.dumps(payload), headers=headers, verify=False)

# If the request went through correctly
if resp.ok:

    # Create dictionary based on response content body
    body = json.loads(resp.content)
    print("Alert created successfully.")
    print("ALERT_UUID=" + body['id'])
    exit(0)

# In case the request returns an error
else:
    print(json.dumps(json.loads(resp.content), indent=4))
    print("Alert Post request failed.")
    exit(1)
