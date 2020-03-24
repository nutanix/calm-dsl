from calm.dsl.cli import get_api_client


client = get_api_client()

name_uuid_map = client.account.get_name_uuid_map({"length": 100})
vmware_accounts = [
    "vm_m1",
    "vm_m2",
    "vm_m3",
    "vm_m4",
    "vm_m5",
    "vm_m6",
    "vm_m7",
    "vm_m8",
    "vm_m9",
    "vm_m10",
    "vm_s2",
    "vm_s3",
    "vm_s4",
    "vm_s5",
    "vm_s6",
    "vm_s7",
    "vm_s8",
    "vm_s9",
    "vm_s10",
    "vmware_account",
    "vmware_n_1",
    "vmware_n_2",
    "vmware_n_3",
    "vmware_n_4",
    "vmware_n_5",
    "vmware_n_6",
    "vmware_n_7",
    "vmware_n_8",
    "vmware_n_9",
    "vmware_n_10",
]

account_references = []
for account in vmware_accounts:
    account_references.append(
        {"kind": "account", "name": account, "uuid": name_uuid_map[account]}
    )

project_name = "Try_Vmware_POC"

project_payload = {
    "project_detail": {
        "name": "Try_Vmware_POC",
        "resources": {"account_reference_list": account_references},
    },
    "user_list": [],
    "user_group_list": [],
    "access_control_policy_list": [],
}

print(project_payload)
