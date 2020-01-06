class GCP:

    STORAGE_DISK_MAP = {
        "local-ssd": "SCRATCH",
        "pd-standard": "PERSISTENT",
        "pd-ssd": "PERSISTENT",
    }
    STORAGE_TYPES = ["pd-standard", "pd-ssd"]
    ADDITIONAL_DISK_STORAGE_TYPES = ["pd-standard", "pd-ssd", "local-ssd"]
    DISK_INTERFACES = ["SCSI", "NVMe"]
    OPERATING_SYSTEMS = ["Linux", "Windows"]
    SCOPES = {
        "Default Access": [
            "https://www.googleapis.com/auth/devstorage.read_only",
            "https://www.googleapis.com/auth/logging.write",
            "https://www.googleapis.com/auth/monitoring.write",
            "https://www.googleapis.com/auth/servicecontrol",
            "https://www.googleapis.com/auth/service.management.readonly",
            "https://www.googleapis.com/auth/trace.append",
        ],
        "Full Access": ["https://www.googleapis.com/auth/cloud-platform"],
    }

    NETWORK_CONFIG_MAP = {"ONE_TO_ONE_NAT": "ONE_TO_ONE_NAT"}

    VERSION = "v1"
    RELATIVE_URL = "gcp/{}".format(VERSION)
    ZONES = "{}/zones".format(RELATIVE_URL)
    MACHINE_TYPES = "{}/machine_types".format(RELATIVE_URL)
    PERSISTENT_DISKS = "{}/persistent_disks".format(RELATIVE_URL)
    DISK_IMAGES = "{}/images".format(RELATIVE_URL)
    NETWORKS = "{}/networks".format(RELATIVE_URL)
    SUBNETWORKS = "{}/subnetworks".format(RELATIVE_URL)
    FIREWALLS = "{}/firewalls".format(RELATIVE_URL)
    SNAPSHOTS = "{}/snapshots".format(RELATIVE_URL)

    PROJECT_ID = "nucalm-devopos"
    COMPUTE_URL = "https://www.googleapis.com/compute/v1"
    PROJECT_URL = "{}/projects/{}".format(COMPUTE_URL, PROJECT_ID)
