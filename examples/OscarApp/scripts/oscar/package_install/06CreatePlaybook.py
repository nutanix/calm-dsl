# Set creds and headers
pc_user = "@@{pc_creds.username}@@"
pc_pass = "@@{pc_creds.secret}@@"
headers = {"Content-Type": "application/json", "Accept": "application/json"}


# Set the url and payload
url = "https://localhost:9440/api/nutanix/v3/action_rules"
payload = {
    "api_version": "3.1",
    "metadata": {"kind": "action_rule", "spec_version": 0},
    "spec": {
        "resources": {
            "name": "@@{calm_application_name}@@ Memory Playbook",
            "description": "Auto-created Playbook by the Calm Application @@{calm_application_name}@@",
            "is_enabled": True,
            "should_validate": True,
            "trigger_list": [
                {
                    "action_trigger_type_reference": {
                        "kind": "action_trigger_type",
                        "uuid": "@@{ALERT_TRIGGER_UUID}@@",
                        "name": "alert_trigger",
                    },
                    "input_parameter_values": {
                        "alert_uid": "@@{ALERT_UID}@@",
                        "severity": '["critical","warning"]',
                        "source_entity_info_list": "[]",
                    },
                }
            ],
            "execution_user_reference": {
                "kind": "user",
                "name": "admin",
                "uuid": "00000000-0000-0000-0000-000000000000",
            },
            "action_list": [
                {
                    "action_type_reference": {
                        "kind": "action_type",
                        "uuid": "@@{ACTION_VMAMA_UUID}@@",
                        "name": "vm_add_memory_action",
                    },
                    "display_name": "VM Add Memory",
                    "input_parameter_values": {
                        "entity_info": "{{trigger[0].source_entity_info}}",
                        "max_memory_size_gib": "12",
                        "memory_size_gib": "2",
                    },
                    "should_continue_on_failure": False,
                    "max_retries": 2,
                },
                {
                    "action_type_reference": {
                        "kind": "action_type",
                        "uuid": "@@{ACTION_RA_UUID}@@",
                        "name": "acknowledge_alert",
                    },
                    "display_name": "Acknowledge Alert",
                    "input_parameter_values": {
                        "alert_entity": "{{trigger[0].alert_entity_info}}"
                    },
                    "should_continue_on_failure": False,
                    "max_retries": 2,
                },
                {
                    "action_type_reference": {
                        "kind": "action_type",
                        "uuid": "@@{ACTION_EA_UUID}@@",
                        "name": "email_action",
                    },
                    "display_name": "Email",
                    "input_parameter_values": {
                        "to_address": "michael@nutanix.com",
                        "subject": "VM @@{Oscar_AHV.name}@@ of Calm App @@{calm_application_name}@@",
                        "message_body": "VM @@{Oscar_AHV.name}@@ of Calm App @@{calm_application_name}@@'s memory was constrained, so it was \nautomatically increased by Prism X-Play.  No action is necessary on your part.\n\nPlaybook Name: {{playbook.playbook_name}}\nCreation Time: {{trigger[0].creation_time}}\nSource Entity Name: {{trigger[0].source_entity_info.name}}\nAlert Name: {{trigger[0].alert_entity_info.name}}",
                    },
                    "should_continue_on_failure": False,
                    "max_retries": 2,
                },
            ],
        }
    },
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
    print("Prism Playbook created successfully")
    print("PLAYBOOK_UUID=" + json.loads(resp.content)["metadata"]["uuid"])
    exit(0)

# In case the request returns an error
else:
    print("Post action_types list request failed", resp.content)
    exit(1)
