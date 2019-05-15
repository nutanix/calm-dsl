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


class BLUEPRINT:
    class STATES:
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"
        DRAFT = "DRAFT"
        ERROR = "ERROR"


class APPLICATION:
    class STATES:
        provisioning = "provisioning"
        stopped = "stopped"
        running = "running"
        error = "error"
        deleted = "deleted"
        deleting = "deleting"
        starting = "starting"
        stopping = "stopping"
        restarting = "restarting"
        busy = "busy"
        timeout = "timeout"
        restarting = "restarting"
