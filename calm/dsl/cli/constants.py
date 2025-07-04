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
        POLICY_EXEC = "POLICY_EXEC"


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


class ENTITY:
    class KIND:
        PROVIDER = "provider"
        RESOURCE_TYPE = "resource_type"


class PROVIDER:
    class STATES:
        DELETED = "DELETED"
        DRAFT = "DRAFT"
        ACTIVE = "ACTIVE"

    class TYPE:
        CUSTOM = "CUSTOM"


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

    WARN_MSG = "Projects associated with MPI should have accounts attached in blueprint for deployment"


class TASKS:
    class TASK_TYPES:
        EXEC = "EXEC"
        SET_VARIABLE = "SET_VARIABLE"
        HTTP = "HTTP"
        RT_OPERATION = "RT_OPERATION"

    class SCRIPT_TYPES:
        POWERSHELL = "npsscript"
        SHELL = "sh"
        ESCRIPT = "static"
        ESCRIPT_PY3 = "static_py3"
        PYTHON = "python_remote"

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


class ROLE:
    PROJECT_ADMIN = "Project Admin"
    DEVELOPER = "Developer"
    CONSUMER = "Consumer"
    OPERATOR = "Operator"


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
                "right_hand_side": {"uuid_list": []},
                "left_hand_side": {"entity_type": "project"},
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
            "permissions": ["view_image"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "image"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permissions": ["view_app_icon"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "app_icon"},
            },
        },
        {
            "permissions": ["view_name_category", "create_or_update_name_category"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "category"},
            },
        },
        {
            "permissions": ["view_environment"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "environment"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
        {
            "permissions": ["view_marketplace_item"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "marketplace_item"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
        {
            "permissions": ["view_role"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "role"},
            },
        },
        {
            "permissions": ["view_directory_service", "search_directory_service"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "directory_service"},
            },
        },
        {
            "permissions": ["view_identity_provider"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "identity_provider"},
            },
        },
        {
            "permissions": ["view_app_task"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_task"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
        {
            "permissions": ["view_app_variable"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "app_variable"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
        {
            "permissions": ["view_resource_type"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "resource_type"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permissions": ["view_custom_provider"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "custom_provider"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
    ]

    CUSTOM_ROLE_SPECIFIC_COLLAB_FILTER = [
        {
            "permissions": ["view_blueprint"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "blueprint"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permissions": ["view_environment"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "environment"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permissions": ["view_marketplace_item"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "marketplace_item"},
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

    # The entities in this collection are by default collab enabled
    PROJECT_COLLAB_CONTEXT = {
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
                "left_hand_side": {"entity_type": "blueprint"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "environment"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "marketplace_item"},
                "right_hand_side": {"collection": "ALL"},
            },
        ],
    }


class ACP_4_2_0:
    class ENTITY_FILTER_EXPRESSION_LIST:
        COMMON = [
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "subnet"},
                "right_hand_side": {"collection": "ALL"},
            },
        ]


class ACP_3_8_1:
    class ENTITY_FILTER_EXPRESSION_LIST:
        COMMON = [
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "container"},
                "right_hand_side": {"collection": "ALL"},
            },
        ]


class ACP_3_8_0:
    class ENTITY_FILTER_EXPRESSION_LIST:
        COMMON = [
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "distributed_virtual_switch"},
                "right_hand_side": {"collection": "ALL"},
            },
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "vm_recovery_point"},
                "right_hand_side": {"collection": "ALL"},
            },
        ]
        PROJECT_ADMIN = [
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "report_config"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            }
        ]

    CUSTOM_ROLE_PERMISSIONS_FILTERS = [
        {
            "permissions": ["view_vm_recovery_point"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "vm_recovery_point"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permissions": ["view_virtual_switch"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "distributed_virtual_switch"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permissions": ["view_report_config"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "report_config"},
                "right_hand_side": {"collection": "SELF_OWNED"},
            },
        },
    ]
    CUSTOM_ROLE_SPECIFIC_COLLAB_FILTER = [
        {
            "permissions": ["view_user"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "user"},
            },
        },
        {
            "permissions": ["view_virtual_machine"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "vm"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
        {
            "permissions": ["view_user_group"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "user_group"},
            },
        },
        {
            "permissions": ["view_runbook"],
            "filter": {
                "operator": "IN",
                "left_hand_side": {"entity_type": "runbook"},
                "right_hand_side": {"collection": "ALL"},
            },
        },
    ]

    PROJECT_COLLAB_FILTER = [
        {
            "operator": "IN",
            "left_hand_side": {"entity_type": "runbook"},
            "right_hand_side": {"collection": "ALL"},
        }
    ]

    PROJECT_ADMIN_SPECIFIC_COLLAB_FILTER = [
        {
            "operator": "IN",
            "left_hand_side": {"entity_type": "vm"},
            "right_hand_side": {"collection": "ALL"},
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
    ]


class ACP_BEFORE_3_8_0:
    class ENTITY_FILTER_EXPRESSION_LIST:
        PROJECT_ADMIN = [
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
        ]

    CUSTOM_ROLE_PERMISSIONS_FILTERS = [
        {
            "permissions": ["view_user"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "user"},
            },
        },
        {
            "permissions": ["view_user_group"],
            "filter": {
                "operator": "IN",
                "right_hand_side": {"collection": "ALL"},
                "left_hand_side": {"entity_type": "user_group"},
            },
        },
    ]


class TEST_SCRIPTS:
    class STATUS:
        SUCCESS = "SUCCESS"
        PENDING = "PENDING"
        RUNNING = "RUNNING"
        ERROR = "ERROR"

    TERMINAL_STATES = [STATUS.SUCCESS, STATUS.ERROR]
    TYPE = ["escript", "shell", "powershell", "python"]


class GLOBAL_VARIABLE:
    class STATES:
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"
        DRAFT = "DRAFT"

    DYNAMIC_VARIABLE_TYPES = ["EXEC_LOCAL", "HTTP_LOCAL", "EXEC_SECRET", "HTTP_SECRET"]
