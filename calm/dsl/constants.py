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
        PROTECTION_POLICY = "app_protection_policy"
        TUNNEL = "tunnel"
        GLOBAL_VARIABLE = "global_variable"

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


class CLOUD_PROVIDERS:
    MIN_SUPPORTED_VERSION = "4.0.0"


class GLOBAL_VARIABLE:
    MIN_SUPPORTED_VERSION = "4.3.0"


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

    class CRED_TYPE:
        BASIC_AUTH = "basic_auth"
        SERVICE_ACCOUNT = "service_account"

    class SERVICE_ACCOUNT:
        FEATURE_MIN_VERSION = "4.3.0"

    STANDARD_TYPES = [
        TYPE.AHV,
        TYPE.AHV_PE,
        TYPE.AWS,
        TYPE.AWS_C2S,
        TYPE.AZURE,
        TYPE.GCP,
        TYPE.VMWARE,
        TYPE.K8S_KARBON,
        TYPE.K8S_VANILLA,
        TYPE.CREDENTIAL_PROVIDER,
        TYPE.CUSTOM_PROVIDER,
        TYPE.NDB,
    ]


class PROVIDER:
    class TYPE:
        GCP = "GCP_VM"
        AZURE = "AZURE_VM"
        AHV = "AHV_VM"
        VMWARE = "VMWARE_VM"
        AWS = "AWS_VM"

    class AHV:
        VLAN_1211 = "vlan1211"

    NAME = {
        TYPE.AHV: "Nutanix",
        TYPE.VMWARE: "Vmware",
        TYPE.AWS: "Aws",
        TYPE.AZURE: "Azure",
        TYPE.GCP: "Gcp",
    }


class QUOTA(object):
    class STATE(object):
        ENABLED = "enabled"
        DISABLED = "disabled"

    class ENTITY(object):
        ACCOUNT = "account"
        CLUSTER = "cluster"
        PROJECT = "project"

    RESOURCES = {"disk": "STORAGE", "vcpu": "VCPUS", "memory": "MEMORY"}

    RESOURCES_WITH_BYTES_UNIT = ["disk", "memory"]


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


class CLOUD_PROVIDER:
    "Provider constants"

    ENTITY_NAME = "CloudProvider"

    class TYPE:
        CUSTOM = "CUSTOM"

    class INFRA_TYPE:
        ONPREM = "on_prem"
        CLOUD = "cloud"

    class ENDPOINT_KIND:
        NUTANIX_PC = "NUTANIX_PC"
        VMWARE = "VMWARE"
        AWS = "AWS"
        GCP = "GCP"
        AZURE = "AZURE"
        CUSTOM = "CUSTOM"
        NONE = "NONE"

    INFRA_TYPES = [INFRA_TYPE.ONPREM, INFRA_TYPE.CLOUD]
    VERIFY_ACTION_NAME = "Verify"

    ENDPOINT_KINDS = [
        ENDPOINT_KIND.NUTANIX_PC,
        ENDPOINT_KIND.VMWARE,
        ENDPOINT_KIND.AWS,
        ENDPOINT_KIND.AZURE,
        ENDPOINT_KIND.GCP,
        ENDPOINT_KIND.CUSTOM,
        ENDPOINT_KIND.NONE,
    ]


class ACTION:
    class TYPE:
        SYSTEM = "system"
        USER = "user"
        WORKFLOW = "workflow"
        FRAGMENT = "fragment"
        RULE = "rule"
        PATCH = "PATCH"
        PROVIDER = "provider"

    TYPES = [
        TYPE.SYSTEM,
        TYPE.USER,
        TYPE.WORKFLOW,
        TYPE.FRAGMENT,
        TYPE.RULE,
        TYPE.PATCH,
        TYPE.PROVIDER,
    ]


class RESOURCE_TYPE:
    "ResourceType constants"

    class TYPE:
        USER = "USER"

    class ACTION_TYPE:
        LIST = "resource_type_list"
        CREATE = "resource_type_create"
        DELETE = "resource_type_delete"
        GENERIC = "resource_type_generic"

    ENTITY_NAME = "ResourceType"

    ACTION_TYPES = [
        ACTION_TYPE.LIST,
        ACTION_TYPE.CREATE,
        ACTION_TYPE.DELETE,
        ACTION_TYPE.GENERIC,
    ]


class CREDENTIAL:
    class CRED_CLASS:
        STATIC = "static"
        DYNAMIC = "dynamic"


class DSL_CONFIG:
    EMPTY_CONFIG_ENTITY_NAME = "-"
    EMPTY_PROJECT_MESSAGE = "Project configuration not available. Use command `calm set config -pj <project_name>` to set it."
    SAAS_PORT = "443"
    SAAS_LOGIN_WARN = "Seems like you are trying to authenticate saas instance. Please provide API key location."


class ENTITY_KIND:
    "'kind' string for different entities"
    APP_ICON = "app_icon"


class VARIABLE:
    class TYPE:
        LOCAL = "LOCAL"
        SECRET = "SECRET"
        INPUT = "INPUT"
        EXTERNAL = "EXTERNAL"
        SYS_LOCAL = "SYS_LOCAL"
        SYS_SECRET = "SYS_SECRET"
        EXEC_LOCAL = "EXEC_LOCAL"
        HTTP_LOCAL = "HTTP_LOCAL"
        EXEC_SECRET = "EXEC_SECRET"
        HTTP_SECRET = "HTTP_SECRET"
        EXEC_EXTERNAL = "EXEC_EXTERNAL"
        HTTP_EXTERNAL = "HTTP_EXTERNAL"
        SYS_EXEC_LOCAL = "SYS_EXEC_LOCAL"
        SYS_HTTP_LOCAL = "SYS_HTTP_LOCAL"
        SYS_EXEC_SECRET = "SYS_EXEC_SECRET"
        SYS_HTTP_SECRET = "SYS_HTTP_SECRET"
        INTERNAL_LOCAL = "INTERNAL_LOCAL"

    class OPTIONS:
        class TYPE:
            EXEC = "EXEC"
            HTTP = "HTTP"
            PREDEFINED = "PREDEFINED"

    SECRET_TYPES = [
        TYPE.SECRET,
        TYPE.EXEC_SECRET,
        TYPE.HTTP_SECRET,
        TYPE.SYS_SECRET,
        TYPE.SYS_EXEC_SECRET,
        TYPE.SYS_HTTP_SECRET,
    ]

    DYNAMIC_TYPES = [
        TYPE.EXEC_LOCAL,
        TYPE.EXEC_SECRET,
        TYPE.HTTP_LOCAL,
        TYPE.HTTP_SECRET,
    ]

    SECRET_ATTRS_TYPE = "SECRET"


class SUBSTRATE:
    POWER_ON = "action_poweron"
    POWER_OFF = "action_poweroff"
    RESTART = "action_restart"
    CHECK_LOGIN = "action_check_login"
    VM_POWER_ACTIONS = {
        "__vm_power_on__": POWER_ON,
        "__vm_power_off__": POWER_OFF,
        "__vm_restart__": RESTART,
        "__vm_check_login__": CHECK_LOGIN,
    }
    VM_POWER_ACTIONS_REV = dict((v, k) for k, v in VM_POWER_ACTIONS.items())
    POWER_ACTION_CAMEL_CASE = {
        POWER_ON: "PowerOn",
        POWER_OFF: "PowerOff",
        RESTART: "Restart",
    }


class TASKS:
    class TASK_TYPES:
        GENERIC_OPERATION = "GENERIC_OPERATION"
        VMOPERATION_NUTANIX = "VMOPERATION_NUTANIX"
        VMOPERATION_VCENTER = "VMOPERATION_VCENTER"
        VMOPERATION_AWS_VM = "VMOPERATION_AWS_VM"
        VMOPERATION_AZURE_VM = "VMOPERATION_AZURE_VM"
        VMOPERATION_GCP_VM = "VMOPERATION_GCP_VM"
        PROVISION_NUTANIX = "PROVISION_NUTANIX"
        PROVISION_VCENTER = "PROVISION_VCENTER"
        ROVISION_AWS_VM = "PROVISION_AWS_VM"
        PROVISION_GCP_VM = "PROVISION_GCP_VM"

        UPDATE_NUTANIX = "UPDATE_NUTANIX"
        CHECK_LOGIN = "CHECK_LOGIN"

        VM_OPERATION = {
            PROVIDER.TYPE.AHV: VMOPERATION_NUTANIX,
            PROVIDER.TYPE.VMWARE: VMOPERATION_VCENTER,
            PROVIDER.TYPE.AWS: VMOPERATION_AWS_VM,
            PROVIDER.TYPE.AZURE: VMOPERATION_AZURE_VM,
            PROVIDER.TYPE.GCP: VMOPERATION_GCP_VM,
        }


class READINESS_PROBE:
    ADDRESS = {
        PROVIDER.TYPE.AHV: "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        PROVIDER.TYPE.VMWARE: "@@{platform.ipAddressList[0]}@@",
        PROVIDER.TYPE.AWS: "@@{public_ip_address}@@",
        PROVIDER.TYPE.AZURE: "@@{platform.publicIPAddressList[0]}@@",
        PROVIDER.TYPE.GCP: "@@{platform.networkInterfaces[0].accessConfigs[0].natIP}@@",
    }


class CONFIG_TYPE:
    class SNAPSHOT:
        AHV = "AHV_SNAPSHOT"
        VMWARE = "VMWARE_SNAPSHOT"
        TYPE = [AHV, VMWARE]

    class RESTORE:
        AHV = "AHV_RESTORE"
        VMWARE = "VMWARE_RESTORE"
        TYPE = [AHV, VMWARE]

    CONFIG_TYPE_MAP = {
        "AHV_VM_snapshot": SNAPSHOT.AHV,
        "VMWARE_VM_snapshot": SNAPSHOT.VMWARE,
        "AHV_VM_restore": RESTORE.AHV,
        "VMWARE_VM_restore": RESTORE.VMWARE,
        "patch": "PATCH",
    }


class PROJECT:
    INTERNAL = "_internal"


# storing it as set because it optimizes the lookup to constant time.
class RESOURCE:
    """Stores and segregates resources based on their API type"""

    NCM = {
        "features/stratos/status",
        "features/approval_policy",
        "features/custom_provider/status",
        "approvals",
        "approval_requests",
        "policies",
        "policy_action_types",
        "policy_events",
        "blueprints",
        "environments",
        "endpoints",
        "runbooks",
        "app_tasks",
        "apps",
        "accounts",
        "app_icons",
        "app_showback",
        "jobs",
        "app_protection_policies",
        "policy_attributes",
        "network_groups",
        "resource_types",
        "providers",
        "quotas",
        "nutanix/v1/vm_recovery_points",
        "tunnels",
        "platform_dependent_fields",
        "blueprints/brownfield_import/vms",
        "calm_marketplace_items",
        "global_variables",
        # AhvNew class resources
        "nutanix/v1/subnets",
        "nutanix/v1/images",
        "nutanix/v1/clusters",
        "nutanix/v1/vpcs",
        "nutanix/v1/groups",
        # AWS api's
        "aws/machine_types",
        "aws/volume_types",
        "aws/availability_zones",
        "aws/mixed_images",
        "images",
        "aws/roles",
        "aws/key_pairs",
        "aws/vpcs",
        "aws/security_groups",
        "aws/subnets",
        "aws/v1/machine_types",
        "aws/v1/volume_types",
        "aws/v1/availability_zones",
        "aws/v1/mixed_images",
        "aws/v1/images",
        "aws/v1/roles",
        "aws/v1/key_pairs",
        "aws/v1/vpcs",
        "aws/v1/security_groups",
        "aws/v1/subnets",
        # Azure api's
        "azure_rm/v1/availability_sets",
        "azure_rm/v1/availability_zones",
        "azure_rm/v1/security_groups",
        "azure_rm/v1/virtual_networks",
        "azure_rm/v1/subnets",
        "azure_rm/v1/resource_groups",
        "azure_rm/v1/locations",
        "azure_rm/v1/vm_sizes",
        "azure_rm/v1/image_publishers",
        "azure_rm/v1/image_offers",
        "azure_rm/v1/image_skus",
        "azure_rm/v1/image_versions",
        "azure_rm/v1/subscription_images",
        "azure_rm/v1/subscriptions",
        "azure_rm/v1/images",
        # GCP api's
        "gcp/v1/zones",
        "gcp/v1/machine_types",
        "gcp/v1/persistent_disks",
        "gcp/v1/images",
        "gcp/v1/networks",
        "gcp/v1/subnetworks",
        "gcp/v1/firewalls",
        "gcp/v1/snapshots",
        # VMWARE api's
        "vmware/v6/datacenter",
        "vmware/v6/template",
        "vmware/v6/library",
        "vmware/v6/library_items",
        "vmware/v6/datastore",
        "vmware/v6/host",
        "vmware/v6/cluster",
        "vmware/v6/storage_pod",
        "vmware/v6/network",
        "vmware/v6/network_adapter",
        "vmware/v6/customization",
        "vmware/v6/timezone",
        "vmware/v6/accounts",
        "vmware/v6/accounts/templates"  # TODO: make it flexible according to account uuid
        "vmware/v6/file_paths",
        "vmware/v6/vm_categories",
        # k8s api's
        "kubernetes/v1/karbon/clusters",
    }

    NON_NCM = {
        "dm/v3/groups",
        "features/policy",
        "projects",
        "projects_internal",
        "tasks",
        "users",
        "user_groups",
        "roles",
        "directory_services",
        "access_control_policies",
        "network_function_chains",
        "services/nucalm/status",
        "categories/AppFamily",
        "mh_vms",
    }

    class ENTITY:
        NCM = {
            "category",
            "marketplace_item",
        }

        NON_NCM = {
            "mh_vm",
        }


class MARKETPLACE:
    """Standard names of marketplace apps"""

    class APP_NAME:
        INFRASTRUCTURE = "Infrastructure"
        NCM = "Nutanix Cloud Manager"

    FETCH_APP_DETAILS_PAYLOAD = {
        "fields": ["app_name", "uuid", "source_marketplace_name", "state", "app_url"],
        "filter": "categories==category_value:Nutanix;categories==category_name:AppFamily;state\u0021=deleted",
    }


class MULTICONNECT:
    PC_OBJ = "pc_conn_obj"
    NCM_OBJ = "ncm_conn_obj"


class MULTIGROUP:
    PC_OBJ = "pc_group"
    NCM_OBJ = "ncm_group"


class FLAGS:
    POLICY_ON_SMSP = False


class TUNNEL:
    API_VERSION = "3.0"
    FEATURE_MIN_VERSION = "4.3.0"

    class KIND:
        ACCOUNT = "tunnel"
        NETWORK_GROUP = "network_group"

    class STATES:
        ACTIVE = "ACTIVE"
        HEALTHY = "HEALTHY"
        UNHEALTHY = "UNHEALTHY"
        DELETED = "DELETED"

    class UI_STATES:
        VALIDATING = "VALIDATING"
        ACTIVE = "ACTIVE"
        ERROR = "ERROR"
        DELETED = "DELETED"

    # Mapping UI states to backend states
    UI_TO_BACKEND_STATE_MAPPING = {
        UI_STATES.VALIDATING: STATES.ACTIVE,
        UI_STATES.ACTIVE: STATES.HEALTHY,
        UI_STATES.ERROR: STATES.UNHEALTHY,
        UI_STATES.DELETED: STATES.DELETED,
    }

    # Mapping backend states to UI states
    BACKEND_TO_UI_STATE_MAPPING = {v: k for k, v in UI_TO_BACKEND_STATE_MAPPING.items()}
