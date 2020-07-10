from calm.dsl.builtins import read_local_file


CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")

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
                                "name": "",
                                "uuid": "c37571b5-51d2-4340-8db0-d62c89ce3c9e",
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
                                "name": "AHV_CENTOS_76",
                                "uuid": "a333ba83-07eb-422d-bf2e-e79c7ea93fa3",
                            },
                            "disk_size_mib": 0,
                        },
                        "1": {
                            "data_source_reference": None,
                            "device_properties": {
                                "device_type": "DISK",
                                "disk_address": {"adapter_type": "SCSI"},
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
        "value": {"min_replicas": "2", "default_replicas": "3", "max_replicas": "4"},
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
