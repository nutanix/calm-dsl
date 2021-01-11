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

    class NUTANIX:
        PC = "nutanix_pc"
        KARBON = "kubernetes_karbon"
    
    class AWS:
        EC2 = "aws"
        C2S = "aws_govcloud"
    
    AZURE = "azure"

    VMWARE = "vmware"

    class KUBERNETES:
        VANILLA = "kubernetes_vanilla"
    
    GCP = "gcp"


class VM:
    """VM Constants"""

    AHV = "AHV_VM"
    AWS = "AWS_VM"
    VMWARE = "VMWARE_VM"
    AZURE = "AZURE_VM"
    GCP = "GCP_VM"
    EXISTING_VM = "EXISTING_VM"
    K8S_POD = "K8S_POD"


class AUTH:
    """auth constants"""

    class KUBERNETES:
        BASIC = "basic"
        CLIENT_CERTIFICATE = "client_certificate"
        CA_CERTIFICATE = "ca_certificate"
