import json
from app_edit_blueprint import TestRuntime
from calm.dsl.log import get_logging_handle
import os
from calm.dsl.builtins import read_local_file
from calm.dsl.store import Version
from distutils.version import LooseVersion as LV

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server_two_vm_example")
MYSQL_PORT = read_local_file(".tests/mysql_port")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NTNX_LOCAL_ACCOUNT = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]
SUBNET_UUID = [
    _["UUID"] for _ in NTNX_LOCAL_ACCOUNT["SUBNETS"] if _["NAME"] == "vlan1211"
][0]

# calm_version
CALM_VERSION = Version.get_version("Calm")

LOG = get_logging_handle(__name__)


def test_json():
    generated_json = json.loads(TestRuntime.json_dumps(pprint=True))
    LOG.info(generated_json)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "app_edit_blueprint.json")
    known_json = json.loads(open(file_path).read())
    for _nd in known_json["substrate_definition_list"][0]["create_spec"]["resources"][
        "nic_list"
    ]:
        _nd["subnet_reference"]["uuid"] = SUBNET_UUID
    known_json["app_profile_list"][0]["patch_list"][0]["attrs_list"][0]["data"][
        "pre_defined_nic_list"
    ][0]["subnet_reference"]["uuid"] = SUBNET_UUID

    known_json["substrate_definition_list"][0]["create_spec"]["resources"][
        "account_uuid"
    ] = None
    generated_json["substrate_definition_list"][0]["create_spec"]["resources"][
        "account_uuid"
    ] = None
    known_json["substrate_definition_list"][0]["create_spec"]["resources"]["disk_list"][
        0
    ]["data_source_reference"]["uuid"] = None
    generated_json["substrate_definition_list"][0]["create_spec"]["resources"][
        "disk_list"
    ][0]["data_source_reference"]["uuid"] = None
    known_json["app_profile_list"][0]["patch_list"][0]["attrs_list"][0]["uuid"] = None
    generated_json["app_profile_list"][0]["patch_list"][0]["attrs_list"][0][
        "uuid"
    ] = None

    if LV(CALM_VERSION) >= LV("3.4.0"):
        for cred in known_json["credential_definition_list"]:
            cred["cred_class"] = "static"

    assert sorted(known_json.items()) == sorted(
        generated_json.items()
    ), "Known Json: {}\nGen Json: {}".format(known_json.items(), generated_json.items())
