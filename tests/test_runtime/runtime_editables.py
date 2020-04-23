runtime_vars = [
    {
        "value": {
            "value": "123"
        },
        "context": "DefaultProfile",
        "name": "foo1"
    },
    {
        "value": {
            "value": "123"
        },
        "context": "PHPPackage",
        "name": "foo"
    }
]

runtime_substrates = [
    {
        "value": {
            "readiness_probe": {
                "connection_type": "SSH",
                "retries": "5",
                "delay_secs": "60",
                "connection_port": 22
            },
            "spec": {
                "name": "vm-@@{calm_array_index}@@-@@{calm_time}@@",
                "resources": {
                    "num_vcpus_per_socket": 1,
                    "boot_config": {
                        "boot_device": {
                            "disk_address": {
                                "device_index": 0,
                                "adapter_type": "SCSI"
                            }
                        },
                        "boot_type": ""
                    },
                    "disk_list": {
                        "0": {
                            "data_source_reference": {
                                "kind": "image",
                                "name": "Centos7",
                                "uuid": "294fa133-be65-4393-aae8-e3b10a0b4293"
                            },
                            "disk_size_mib": 0
                        }
                    }
                }
            }
        },
        "context": "MySQLDeployment",
        "name": "AHVVMforMySQL"
    }
]