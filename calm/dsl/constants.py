"""
    Calm-DSL constants
"""


class CACHE:
    """Cache constants"""

    class ENTITY:
        AHV_SUBNET = "ahv_subnet"
        AHV_DISK_IMAGE = "ahv_disk_image"
        ACCOUNT = "account"
        PROJECT = "project"
        USER = "user"
        ROLE = "role"
        DIRECTORY_SERVICE = "directory_service"
        USER_GROUP = "user_group"
        AHV_NETWORK_FUNCTION_CHAIN = "ahv_network_function_chain"


class PROVIDER:
    """Provider constants"""

    class ACCOUNT:
        NUTANIX = "nutanix_pc"
        AWS = "aws"
        VMWARE = "vmware"
        AZURE = "azure"
        GCP = "gcp"
        K8S = "k8s"

    class VM:
        AHV = "AHV_VM"
        AWS = "AWS_VM"
        VMWARE = "VMWARE_VM"
        AZURE = "AZURE_VM"
        GCP = "GCP_VM"
        EXISTING_VM = "EXISTING_VM"
        K8S_POD = "K8S_POD"
