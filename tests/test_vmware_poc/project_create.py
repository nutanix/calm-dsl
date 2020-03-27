import os
import inspect
import sys
import json
import click
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
    "vm_m11",
    "vm_m12",
    "vm_m13",
    "vm_m14",
    "vm_m15",
    "vm_m16",
    "vm_m17",
    "vm_m18",
    "vm_m19",
    "vm_m20",
    "vm_n11",
    "vm_n12",
    "vm_n13",
    "vm_n14",
    "vm_n15",
    "vm_n16",
    "vm_n17",
    "vm_n18",
    "vm_n19",
    "vm_n20",
]


click.echo("verifying accounts")
account_references = []
for account in vmware_accounts:
    account_references.append(
        {"kind": "account", "name": account, "uuid": name_uuid_map[account]}
    )
    client.account.verify(name_uuid_map[account])
click.echo("accounts verified")


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

with open('/Users/abhijeet.kaurav/ocalm-dsl/tests/test_vmware_poc/specs/project_spec.json', "w+") as fd:
    fd.write(json.dumps(project_payload, indent=4, separators=(",", ": ")))
