class RUNLOG:
    class STATUS:
        SUCCESS = "SUCCESS"
        PENDING = "PENDING"
        RUNNING = "RUNNING"
        FAILURE = "FAILURE"
        WARNING = "WARNING"
        ERROR = "ERROR"
        APPROVAL = "APPROVAL"
        APPROVAL_FAILED = "APPROVAL_FAILED"
        ABORTED = "ABORTED"
        ABORTING = "ABORTING"
        SYS_FAILURE = "SYS_FAILURE"
        SYS_ERROR = "SYS_ERROR"
        SYS_ABORTED = "SYS_ABORTED"
        ALREADY_RUN = "ALREADY_RUN"
        TIMEOUT = "TIMEOUT"
        INPUT = "INPUT"
        CONFIRM = "CONFIRM"
        PAUSED = "PAUSED"

    TERMINAL_STATES = [
        STATUS.SUCCESS,
        STATUS.FAILURE,
        STATUS.APPROVAL_FAILED,
        STATUS.WARNING,
        STATUS.ERROR,
        STATUS.ABORTED,
        STATUS.SYS_FAILURE,
        STATUS.SYS_ERROR,
        STATUS.SYS_ABORTED,
    ]
    FAILURE_STATES = [
        STATUS.FAILURE,
        STATUS.APPROVAL_FAILED,
        STATUS.WARNING,
        STATUS.ERROR,
        STATUS.ABORTED,
        STATUS.SYS_FAILURE,
        STATUS.SYS_ERROR,
        STATUS.SYS_ABORTED,
    ]


class JOBS:
    class STATES:
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"
        INACTIVE = "INACTIVE"


class JOBINSTANCES:
    class STATES:
        SCHEDULED = "SCHEDULED"
        RUNNING = "RUNNING"
        SKIPPED = "SKIPPED"
        FAILED = "FAILED"


class RUNBOOK:
    class STATES:
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"
        DRAFT = "DRAFT"
        ERROR = "ERROR"


class ENDPOINT:
    class STATES:
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"
        DRAFT = "DRAFT"
        ERROR = "ERROR"

    class TYPES:
        HTTP = "HTTP"
        WINDOWS = "Windows"
        LINUX = "Linux"

    class VALUE_TYPES:
        VM = "VM"
        IP = "IP"


class BLUEPRINT:
    class STATES:
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"
        DRAFT = "DRAFT"
        ERROR = "ERROR"


class POLICY:
    class STATES:
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"
        DELETED = "DELETED"
        DRAFT = "DRAFT"


class APPROVAL_REQUEST:
    class STATES:
        PENDING = "PENDING"
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"
        EXPIRED = "EXPIRED"
        ABORTED = "ABORTED"

    TERMINAL_STATES = [
        STATES.APPROVED,
        STATES.REJECTED,
        STATES.EXPIRED,
        STATES.ABORTED,
    ]


class APPLICATION:
    class STATES:
        PROVISIONING = "provisioning"
        STOPPED = "stopped"
        RUNNING = "running"
        ERROR = "error"
        DELETED = "deleted"
        DELETING = "deleting"
        STARTING = "starting"
        STOPPING = "stopping"
        RESTARTING = "restarting"
        BUSY = "busy"
        TIMEOUT = "timeout"
        RESTARTING = "restarting"
        UPDATING = "updating"


class ACCOUNT:
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


class SINGLE_INPUT:
    class TYPE:
        TEXT = "text"
        PASSWORD = "password"
        CHECKBOX = "checkbox"
        SELECT = "select"
        SELECTMULTIPLE = "selectmultiple"
        DATE = "date"
        TIME = "time"
        DATETIME = "datetime"

    VALID_TYPES = [
        TYPE.TEXT,
        TYPE.PASSWORD,
        TYPE.CHECKBOX,
        TYPE.SELECT,
        TYPE.SELECTMULTIPLE,
        TYPE.DATE,
        TYPE.TIME,
        TYPE.DATETIME,
    ]


class SYSTEM_ACTIONS:
    CREATE = "create"
    START = "start"
    RESTART = "restart"
    UPDATE = "update"
    STOP = "stop"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"


class MARKETPLACE_ITEM:
    class TYPES:
        BLUEPRINT = "blueprint"
        RUNBOOK = "runbook"

    class STATES:
        PENDING = "PENDING"
        ACCEPTED = "ACCEPTED"
        REJECTED = "REJECTED"
        PUBLISHED = "PUBLISHED"

    class SOURCES:
        GLOBAL = "GLOBAL_STORE"
        LOCAL = "LOCAL"


class TASKS:
    class TASK_TYPES:
        EXEC = "EXEC"
        SET_VARIABLE = "SET_VARIABLE"
        HTTP = "HTTP"

    class SCRIPT_TYPES:
        POWERSHELL = "npsscript"
        SHELL = "sh"
        ESCRIPT = "static"

    class STATES:
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"
        DRAFT = "DRAFT"


class ERGON_TASK:
    class STATUS:
        QUEUED = "QUEUED"
        RUNNING = "RUNNING"
        ABORTED = "ABORTED"
        SUCCEEDED = "SUCCEEDED"
        SUSPENDED = "SUSPENDED"
        FAILED = "FAILED"

    TERMINAL_STATES = [
        STATUS.SUCCEEDED,
        STATUS.FAILED,
        STATUS.ABORTED,
        STATUS.SUSPENDED,
    ]

    FAILURE_STATES = [STATUS.FAILED, STATUS.ABORTED, STATUS.SUSPENDED]


class ACP:
    class ENTITY_FILTER_EXPRESSION_LIST:
        DEVELOPER = [
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "image"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "marketplace_item"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "app_icon"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "category"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_task"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_variable"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "virtual_network"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "resource_type"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "custom_provider"},
                "right_hand_side": {"collection": "ALL"},
            },
        ]

        OPERATOR = [
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "app_icon"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "category"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "resource_type"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "custom_provider"},
                "right_hand_side": {"collection": "ALL"},
            },
        ]

        CONSUMER = [
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "image"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "marketplace_item"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "app_icon"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "category"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_task"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_variable"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "virtual_network"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "resource_type"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "custom_provider"},
                "right_hand_side": {"collection": "ALL"},
            },
        ]

        PROJECT_ADMIN = [
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "image"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "marketplace_item"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "directory_service"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "role"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"uuid_list": []},
                "left_hand_side": {"entity_type": "project"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "user"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "user_group"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "SELF_OWNED"},
                "left_hand_side": {"entity_type": "environment"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "app_icon"},
            },
            {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "category"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_task"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_variable"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "virtual_network"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "resource_type"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "custom_provider"},
                "right_hand_side": {"collection": "ALL"},
            },
        ]

    CUSTOM_ROLE_PERMISSIONS_FILTERS = [
        {
            "permission": "view_image",
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "image"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permission": "view_app_icon",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "app_icon"},
            },
        },
        {
            "permission": "view_name_category",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "category"},
            },
        },
        {
            "permission": "create_or_update_name_category",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "category"},
            },
        },
        {
            "permission": "view_environment",
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "environment"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
        {
            "permission": "view_marketplace_item",
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "marketplace_item"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
        {
            "permission": "view_user",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "user"},
            },
        },
        {
            "permission": "view_user_group",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "user_group"},
            },
        },
        {
            "permission": "view_role",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "role"},
            },
        },
        {
            "permission": "view_directory_service",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "directory_service"},
            },
        },
        {
            "permission": "search_directory_service",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "directory_service"},
            },
        },
        {
            "permission": "view_identity_provider",
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "identity_provider"},
            },
        },
        {
            "permission": "view_app_task",
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_task"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
        {
            "permission": "view_app_variable",
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_variable"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
        {
            "permission": "view_image",
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "resource_type"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permission": "view_image",
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "custom_provider"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
    ]

    DEFAULT_CONTEXT = {
        "scope_filter_expression_list": [
            {
                "operator": "IN",
                "left_hand_side": "PROJECT",
                "right_hand_side": {"uuid_list": []},
            }
        ],
        "entity_filter_expression_list": [
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "ALL"},
                "right_hand_side": {"collection": "ALL"},
            }
        ],
    }
