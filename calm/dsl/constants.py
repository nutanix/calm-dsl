"""
    Calm-DSL constants
"""


class CACHE:
    """Cache constants"""

    NDB = "ndb"
    KEY_SEPARATOR = "_"

    class ENTITY:
        AHV_CLUSTER = "ahv_cluster"
        AHV_VPC = "ahv_vpc"
        AHV_SUBNET = "ahv_subnet"
        AHV_DISK_IMAGE = "ahv_disk_image"
        ACCOUNT = "account"
        PROVIDER = "provider"
        RESOURCE_TYPE = "resource_type"
        PROJECT = "project"
        USER = "user"
        ROLE = "role"
        DIRECTORY_SERVICE = "directory_service"
        USER_GROUP = "user_group"
        AHV_NETWORK_FUNCTION_CHAIN = "ahv_network_function_chain"
        ENVIRONMENT = "environment"
        POLICY_EVENT = "policy_event"
        POLICY_ACTION_TYPE = "policy_action_type"
        POLICY_ATTRIBUTES = "policy_attributes"
        APP_PROTECTION_POLICY = "app_protection_policy"

    API_ENTITY_KIND_MAP = {
        "cluster": ENTITY.AHV_CLUSTER,
        "vpc": ENTITY.AHV_VPC,
        "subnet": ENTITY.AHV_SUBNET,
        "image": ENTITY.AHV_DISK_IMAGE,
        "account": ENTITY.ACCOUNT,
    }

    class NDB_ENTITY:
        DATABASE = "database"
        PROFILE = "profile"
        SLA = "sla"
        TIME_MACHINE = "timemachine"
        TAG = "tag"
        CLUSTER = "cluster"
        SNAPSHOT = "snapshot"


PROVIDER_ACCOUNT_TYPE_MAP = {
    "AWS_VM": "aws",
    "VMWARE_VM": "vmware",
    "AHV_VM": "nutanix_pc",
    "AZURE_VM": "azure",
    "GCP_VM": "gcp",
}


class PROJECT_TASK:
    class STATUS:
        PENDING = "pending"
        RUNNING = "running"
        ABORTED = "aborted"
        SUCCESS = "success"
        SUSPENDED = "waiting"
        FAILURE = "failure"

    TERMINAL_STATES = [
        STATUS.ABORTED,
        STATUS.SUCCESS,
        STATUS.FAILURE,
    ]

    NON_TERMINAL_STATES = [
        STATUS.RUNNING,
        STATUS.PENDING,
    ]

    FAILURE_STATES = [STATUS.ABORTED, STATUS.SUSPENDED, STATUS.FAILURE]


class POLICY:
    """Policy related constants"""

    MIN_SUPPORTED_VERSION = "3.1.0"
    APPROVAL_POLICY_MIN_SUPPORTED_VERSION = "3.5.0"

    class APPROVER_SET:
        """Types of approver set for approval policy"""

        ANY = "ANY"
        ALL = "ALL"

    class EVENT:
        """Types of events supported in policy"""

        class APP:
            LAUNCH = "LAUNCH"
            DAY_TWO_OPERATION = "DAY_TWO_OPERATION"

        class RUNBOOK:
            EXECUTE = "EXECUTE"

    class ACTION_TYPE:
        """Supported Action Types"""

        APPROVAL = "APPROVAL"
        QUOTA_CHECK = "QUOTA_CHECK"
        EMAIL = "EMAIL"


class STRATOS:
    """stratos related constants"""

    MIN_SUPPORTED_VERSION = "3.7.0"

    class PROVIDER:
        """Stratos added providers"""

        NDB = "NDB"


class NETWORK_GROUP_TUNNEL_TASK:
    class STATUS:
        SUCCESS = "Succeeded"
        FAILURE = "Failed"
        ABORTED = "Aborted"
        QUEUED = "Queued"

    TERMINAL_STATES = [
        STATUS.ABORTED,
        STATUS.SUCCESS,
        STATUS.FAILURE,
    ]
    FAILURE_STATES = [STATUS.ABORTED, STATUS.FAILURE]


class ACCOUNT:
    """Account constants"""

    class STATES:
        DELETED = "DELETED"
        VERIFIED = "VERIFIED"
        NOT_VERIFIED = "NOT_VERIFIED"
        VERIFY_FAILED = "VERIFY_FAILED"
        DRAFT = "DRAFT"
        ACTIVE = "ACTIVE"
        UNSAVED = "UNSAVED"

    class TYPE:
        AHV = "nutanix_pc"
        AHV_PE = "nutanix"
        AWS = "aws"
        AWS_C2S = "aws_govcloud"
        AZURE = "azure"
        GCP = "gcp"
        VMWARE = "vmware"
        K8S_KARBON = "k8s_karbon"
        K8S_VANILLA = "k8s_vanilla"
        CREDENTIAL_PROVIDER = "credential_provider"
        NDB = "NDB"
        CUSTOM_PROVIDER = "custom_provider"


class PROVIDER:
    class TYPE:
        GCP = "GCP_VM"
        AZURE = "AZURE_VM"
        AHV = "AHV_VM"
        VMWARE = "VMWARE_VM"
        AWS = "AWS_VM"


class QUOTA(object):
    class STATE(object):
        ENABLED = "enabled"
        DISABLED = "disabled"

    class ENTITY(object):
        ACCOUNT = "account"
        CLUSTER = "cluster"
        PROJECT = "project"


class ENTITY:
    "Entity constants"

    class OPENAPI_TYPE:
        AHV = "app_ahv_account"
        AZURE = "app_azure_account"
        AWS = "app_aws_account"
        AWS_C2S = "app_aws_c2s_account"
        K8S_VANILLA = "app_k8s_vanilla_account"
        K8S_KARBON = "app_k8s_karbon_account"
        VMWARE = "app_vmware_account"
        GCP = "app_gcp_account"
        CREDENTIAL_PROVIDER = "app_credential_provider_account"
        CUSTOM_PROVIDER = "app_custom_provider_account"


class DSL_CONFIG:
    EMPTY_PROJECT_NAME = "-"
    EMPTY_PROJECT_MESSAGE = "Project configuration not available. Use command `calm set config -pj <project_name>` to set it."
