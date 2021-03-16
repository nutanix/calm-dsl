import json

from calm.dsl.builtins import read_local_file
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE


CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_HM = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_HADOOP_MASTER"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]  # TODO change network constants

# projects
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]

NTNX_ACCOUNT = PROJECT["ACCOUNTS"]["NUTANIX_PC"][0]
NTNX_ACCOUNT_NAME = PROJECT["ACCOUNTS"]["NUTANIX_PC"][0]["NAME"]
NTNX_ACCOUNT_UUID = PROJECT["ACCOUNTS"]["NUTANIX_PC"][0]["UUID"]

image_cache_data = Cache.get_entity_data(
    entity_type=CACHE.ENTITY.AHV_DISK_IMAGE,
    name=CENTOS_HM,
    image_type="DISK_IMAGE",
    account_uuid=NTNX_ACCOUNT_UUID,
)
CENTOS_HM_UUID = image_cache_data.get("uuid", "")

subnet_cache_data = Cache.get_entity_data(
    entity_type=CACHE.ENTITY.AHV_SUBNET,
    name=NETWORK1,
    account_uuid=NTNX_ACCOUNT_UUID,
)
NETWORK1_UUID = subnet_cache_data.get("uuid", "")

variable_list = [
    {"value": {"value": "foo1_new_val"}, "context": "DefaultProfile", "name": "foo1"},
    {"value": {"value": "foo2_new_val"}, "context": "DefaultProfile", "name": "foo2"},
]

substrate_list = [
    {
        "value": {
            "readiness_probe": {"retries": "7", "connection_port": 22},
            "spec": {
                "resources": {
                    "nic_list": {
                        "0": {
                            "subnet_reference": {
                                "kind": "subnet",
                                "name": NETWORK1,
                                "uuid": NETWORK1_UUID,
                            }
                        }
                    },
                    "serial_port_list": {
                        "0": {"is_connected": False},
                        "1": {"is_connected": True},
                    },
                    "num_vcpus_per_socket": 2,
                    "num_sockets": 2,
                    "memory_size_mib": 1024,
                    "boot_config": {
                        "boot_device": {
                            "disk_address": {"device_index": 0, "adapter_type": "SCSI"}
                        },
                        "boot_type": "",
                    },
                    "guest_customization": None,
                    "disk_list": {
                        "0": {
                            "data_source_reference": {
                                "kind": "image",
                                "name": CENTOS_HM,
                                "uuid": CENTOS_HM_UUID,
                            },
                            "disk_size_mib": 0,
                        },
                        "1": {
                            "data_source_reference": None,
                            "device_properties": {
                                "device_type": "DISK",
                                "disk_address": {"adapter_type": "PCI"},
                            },
                            "disk_size_mib": 10240,
                        },
                    },
                },
                "name": "@@{calm_application_name}@@-@@{calm_array_index}@@",
                "categories": '{"AppFamily":"Backup"}',
            },
        },
        "context": "MySQLDeployment",  # Will be ignored
        "name": "AhvSubstrate",
    }
]

deployment_list = [
    {
        "value": {"min_replicas": "1", "default_replicas": "1", "max_replicas": "2"},
        "context": "DefaultProfile",  # Will be ignored
        "name": "AhvDeployment",
    }
]

credential_list = [
    {
        "value": {
            "username": CRED_USERNAME,
            "secret": {"attrs": {"is_secret_modified": True}, "value": CRED_PASSWORD},
        },
        "context": "AhvSubstrate",  # will be ignored
        "name": "default cred",
    }
]
