# Set creds, headers, and URL
era_user = "@@{era_creds.username}@@"
era_pass = "@@{era_creds.secret}@@"
headers = {"Content-Type": "application/json", "Accept": "application/json"}
url = "https://@@{era_ip}@@:8443/era/v0.8/operations/@@{CREATE_OPERATION_ID}@@"

# Monitor the operation
for x in range(20):

    print("Sleeping for 60 seconds.")
    sleep(60)
    resp = urlreq(
        url, verb="GET", auth="BASIC", user=era_user, passwd=era_pass, headers=headers
    )
    print(
        "Percentage Complete: {0}".format(
            json.loads(resp.content)["percentageComplete"]
        )
    )

    # If complete, break out of loop
    if json.loads(resp.content)["percentageComplete"] == "100":
        break

# If the operation did not complete within 20 minutes, assume it's not successful and error out
if json.loads(resp.content)["percentageComplete"] != "100":
    print("Get Operation ID timed out", json.dumps(json.loads(resp.content), indent=4))
    exit(1)

# Get the newly provision DB Entity Name and set it to a variable
print("DB_ENTITY_NAME={0}".format(json.loads(resp.content)["entityName"]))
