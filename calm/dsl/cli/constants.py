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


class BLUEPRINT:
    class STATES:
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"
        DRAFT = "DRAFT"
        ERROR = "ERROR"


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


class ACCOUNT:
    class STATES:
        DELETED = "DELETED"
        VERIFIED = "VERIFIED"
        NOT_VERIFIED = "NOT_VERIFIED"
        VERIFY_FAILED = "VERIFY_FAILED"
        DRAFT = "DRAFT"
        ACTIVE = "ACTIVE"
        UNSAVED = "UNSAVED"

    class TYPES:
        AWS = "aws"
        AHV = "nutanix"
        KUBERNETES = "k8s"
        AZURE = "azure"
        GCP = "gcp"
        VMWARE = "vmware"


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
    STOP = "stop"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"


class MARKETPLACE_BLUEPRINT:
    class STATES:
        PENDING = "PENDING"
        ACCEPTED = "ACCEPTED"
        REJECTED = "REJECTED"
        PUBLISHED = "PUBLISHED"

    class SOURCES:
        GLOBAL = "GLOBAL_STORE"
        LOCAL = "LOCAL"


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
