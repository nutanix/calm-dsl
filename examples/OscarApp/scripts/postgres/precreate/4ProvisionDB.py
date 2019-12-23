# Set creds and headers
era_user = "@@{era_creds.username}@@"
era_pass = "@@{era_creds.secret}@@"
headers = {"Content-Type": "application/json", "Accept": "application/json"}

# Set the URL and payload
url = "https://@@{era_ip}@@:8443/era/v0.8/databases/provision"
payload = {
    "databaseName": "@@{DB_NAME}@@",
    "databaseType": "postgres_database",
    "databaseDescription": "Postgres database provisioned by Calm Application @@{calm_application_name}@@",
    "clusterId": "@@{CLUSTER_ID}@@",
    "softwareProfileId": "@@{SOFTWARE_PROF_ID}@@",
    "computeProfileId": "@@{COMPUTE_PROF_ID}@@",
    "networkProfileId": "@@{NETWORK_PROF_ID}@@",
    "dbParameterProfileId": "@@{DB_PARAM_ID}@@",
    "provisionInfo": [
        {"name": "application_type", "value": "postgres_database"},
        {"name": "listener_port", "value": "5432"},
        {"name": "database_size", "value": "200"},
        {"name": "working_dir", "value": "/tmp"},
        {"name": "auto_tune_staging_drive", "value": True},
        {"name": "db_password", "value": "@@{db_password}@@"},
        {"name": "dbserver_name", "value": "PostgreSQL-@@{calm_time}@@"},
        {
            "name": "dbserver_description",
            "value": "Postgres database server provisioned by Calm Application @@{calm_application_name}@@",
        },
        {"name": "ssh_public_key", "value": "@@{db_public_key}@@"},
    ],
    "timeMachineInfo": {
        "name": "PostgreSQL-@@{calm_time}@@_TM",
        "description": "PostgreSQL-@@{calm_time}@@ time machine",
        "slaId": "@@{SLA_ID}@@",
        "schedule": {
            "continuousSchedule": {
                "enabled": True,
                "logBackupInterval": 30,
                "snapshotsPerDay": 30,
            },
            "snapshotTimeOfDay": {"hours": 1, "minutes": 0, "seconds": 0},
            "weeklySchedule": {"enabled": True, "dayOfWeek": "SUNDAY"},
            "monthlySchedule": {"enabled": True, "dayOfMonth": 1},
            "quartelySchedule": {
                "enabled": True,
                "startMonth": "JANUARY",
                "dayOfMonth": 1,
            },
            "yearlySchedule": {"enabled": False, "month": "DECEMBER", "dayOfMonth": 1},
        },
    },
}

# Make the call and set the response operation ID to the variable
resp = urlreq(
    url,
    verb="POST",
    auth="BASIC",
    user=era_user,
    passwd=era_pass,
    params=json.dumps(payload),
    headers=headers,
)
if resp.ok:
    print("CREATE_OPERATION_ID={0}".format(json.loads(resp.content)["operationId"]))
else:
    print(
        "Post Database create request failed",
        json.dumps(json.loads(resp.content), indent=4),
    )
    exit(1)
