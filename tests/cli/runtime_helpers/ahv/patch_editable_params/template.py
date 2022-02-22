patch_attrs = [
    {
        "patch_attributes_uuid": "PATCH_ATTRS_UUID",
        "vm_config": {
            "num_sockets": 2,
            "num_vcpus_per_socket": 2,
            "memory_size_mib": 2048,
        },
        "nics": {
            "delete": [1],
            "add": [
                {
                    "identifier": "A1",
                    "subnet_reference": {
                        "kind": "subnet",
                        "type": "",
                        "name": "",
                        "uuid": "NIC_UUID",
                    },
                }
            ],
        },
        "disks": {
            "delete": [2],
            "modify": [
                {
                    "device_properties": {
                        "disk_address": {
                            "adapter_type": "SCSI",
                            "device_index": 1,
                        }
                    },
                    "disk_size_mib": {
                        "value": 11264,
                    },
                }
            ],
            "add": [
                {
                    "index": 3,
                    "disk_size_mib": {"value": 13312},
                }
            ],
        },
        "categories": {
            "add": ["AppType:Default", "OSType:Linux", "Cat:Subcat"],
            "delete": [1, 2, 3, 4],
        },
    }
]
