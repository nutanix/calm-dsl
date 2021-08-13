"""
    Calm-DSL constants
"""


class CACHE:
    """Cache constants"""

    class ENTITY:
        AHV_CLUSTER = "ahv_cluster"
        AHV_VPC = "ahv_vpc"
        AHV_SUBNET = "ahv_subnet"
        AHV_DISK_IMAGE = "ahv_disk_image"
        ACCOUNT = "account"
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


class POLICY:
    """Policy related constants"""

    MIN_SUPPORTED_VERSION = "3.1.0"

    class APPROVER_SET:
        """Types of approver set for approval policy"""

        ANY = "ANY"
        ALL = "ALL"

    class EVENT:
        """Types of events supported in policy"""

        class APP:
            LAUNCH = "LAUNCH"
            DAY_TWO_OPERATION = "DAY_TWO_OPERATION"
            PRE_CREATE = "PRE_CREATE"

        class RUNBOOK:
            EXECUTE = "EXECUTE"

    class ACTION_TYPE:
        """Supported Action Types"""

        APPROVAL = "APPROVAL"
        QUOTA_CHECK = "QUOTA_CHECK"
        EMAIL = "EMAIL"
