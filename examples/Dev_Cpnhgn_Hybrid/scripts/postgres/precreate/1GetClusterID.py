# Set creds and headers
era_user = "@@{era_creds.username}@@"
era_pass = "@@{era_creds.secret}@@"
headers = {"Content-Type": "application/json", "Accept": "application/json"}

# Set TIME variable
print('TIME=@@{calm_time("%Y%m%d%H%M")}@@')

# Get Cluster ID
url = "https://@@{era_ip}@@:8443/era/v0.8/clusters"
resp = urlreq(
    url, verb="GET", auth="BASIC", user=era_user, passwd=era_pass, headers=headers
)
if resp.ok:
    print("CLUSTER_ID={0}".format(json.loads(resp.content)[0]["id"]))
else:
    print(
        "Get Cluster ID request failed", json.dumps(json.loads(resp.content), indent=4)
    )
    exit(1)
