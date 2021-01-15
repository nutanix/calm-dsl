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


'''class PROVIDER:
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
'''

class PROVIDER:

    NUTANIX = "NUTANIX"
    AWS = "AWS"
    AWS_C2S = "AWS_C2S"
    AZURE = "AZURE"
    VMWARE = "VMWARE"
    GCLOUD = "GCLOUD"
    KUBERNETES = "KUBERNETES"


class PROVIDER_RESOURCE:
    class NUTANIX:
        VM = "VM"
        KARBON = "KARBON"
    
    class AWS:
        EC2 = "EC2"
    
    class AWS_C2S:
        EC2 = "EC2"
    
    class GCLOUD:
        GCP = "GCP"
    
    class AZURE:
        VM = "VM"
    
    class VMWARE:
        VM = "VM"
    
    class KUBERNETES:
        VANILLA = "VANILLA"

    __default__ = {
        PROVIDER.NUTANIX : NUTANIX.VM,
        PROVIDER.AWS : AWS.EC2,
        PROVIDER.AWS_C2S : AWS_C2S.EC2,
        PROVIDER.GCLOUD : GCLOUD.GCP,
        PROVIDER.AZURE : AZURE.VM,
        PROVIDER.VMWARE : VMWARE.VM,
        PROVIDER.KUBERNETES: KUBERNETES.VANILLA
    }


# Used for conversion of (provider_type, resource_type) to calm_account_type
ACCOUNT_TYPE_MAP = {
    PROVIDER.NUTANIX : {
        PROVIDER_RESOURCE.NUTANIX.VM : "nutanix_pc",
        PROVIDER_RESOURCE.NUTANIX.KARBON : "kubernetes",
    },
    PROVIDER.AWS : {
        PROVIDER_RESOURCE.AWS.EC2 : "aws",
    },
    PROVIDER.AWS_C2S: {
        PROVIDER_RESOURCE.AWS_C2S.EC2 : "aws_govcloud",
    },
    PROVIDER.AZURE: {
        PROVIDER_RESOURCE.AZURE.VM : "azure",
    },
    PROVIDER.VMWARE: {
        PROVIDER_RESOURCE.VMWARE.VM : "vmware",
    },
    PROVIDER.GCLOUD: {
        PROVIDER_RESOURCE.GCLOUD.GCP : "gcp",
    },
    PROVIDER.KUBERNETES: {
        PROVIDER_RESOURCE.KUBERNETES.VANILLA: "kubernetes"
    }
}


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
