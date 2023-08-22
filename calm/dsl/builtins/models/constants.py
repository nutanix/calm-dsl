class TASK_INPUT:
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


HIDDEN_SUFFIX = "__hidden"


class NutanixDB:
    """Nutanix DB class constant for dsl models"""

    NDB = "NDB"

    class RESOURCE_TYPE:
        """Resource type Constant for Nutanix DB models"""

        POSTGRES_DATABASE = "Postgres Database Instance"
        PROFILE = "Profile"
        SLA = "SLA"
        CLUSTER = "Cluster"
        TIME_MACHINE = "Time Machine"
        SNAPSHOT = "Snapshot"

    class ACTION_TYPE:
        """Action type Constant support by Resource_type of Nutanix DB models"""

        CREATE = "Create"
        DELETE = "Delete"
        RESTORE_FROM_TIME_MACHINE = "Restore from Time Machine"
        CREATE_SNAPSHOT = "Create Snapshot"
        CLONE = "Clone from Time Machine"

    class PROFILE:
        """Profile Constant for Nutanix DB models"""

        SOFTWARE = "Software"
        SOFTWARE_PROFILE_VERSION = "Software_version"
        COMPUTE = "Compute"
        NETWORK = "Network"
        DATABASE_PARAMETER = "Database_Parameter"

        class ENGINE:
            """Engine Constant for Profiles of Nutanix DB models"""

            POSTGRES_DATABASE = "postgres_database"

    class Tag:
        """Supported Tag Constant for Nutanix DB models resource_type"""

        DATABASE = "Database"

    class Attrs:
        """NDB constant attrs"""

        CLUSTER = "cluster"
        TAGS = "tags"
        DATABASE = "database"
        SNAPSHOT_WITH_TIMESTAMP = "snapshot_with_timeStamp"
        TIME_MACHINE = "time_machine"
        SLA = "sla"
        TIME_ZONE = "time_zone"

        class Profile:
            """Supported Profile for Nutanix DB models"""

            SOFTWARE_PROFILE = "software_profile"
            SOFTWARE_PROFILE_VERSION = "software_profile_version"
            COMPUTE_PROFILE = "compute_profile"
            NETWORK_PROFILE = "network_profile"
            DATABASE_PARAMETER_PROFILE = "database_parameter_profile"

        class Tag:
            """Supported Tag Constant for Nutanix DB models"""

            DATABASE = "database"
            TIME_MACHINE = "time_machine"
            CLONE = "clone"
            DATABASE_SERVER = "database_server"
