class IterableConstants:
    @classmethod
    def ALL(cls):
        """
        Schematics expect list or tuple strictly; not just iterable.
        :returns: a list of all public attr
        """
        attrs = []
        for field in vars(cls):
            if not field.startswith("__"):
                attrs.append(getattr(cls, field))
        return attrs


class CONFIG:
    class CONNECTION(IterableConstants):
        CONNECTION_TIMEOUT = "connection_timeout"
        RETRIES_ENABLED = "retries_enabled"
        READ_TIMEOUT = "read_timeout"

    class LOG(IterableConstants):
        LEVEL = "level"

    class STRATOS(IterableConstants):
        STATUS = "stratos_status"

    class CLOUD_PROVIDERS(IterableConstants):
        STATUS = "cp_status"

    class APPROVAL_POLICY(IterableConstants):
        STATUS = "approval_policy_status"

    class POLICY(IterableConstants):
        STATUS = "policy_status"

    class SERVER(IterableConstants):
        HOST = "pc_ip"
        PORT = "pc_port"
        USERNAME = "pc_username"
        PASSWORD = "pc_password"
        API_KEY_LOCATION = "api_key_location"

    class NCM_SERVER(IterableConstants):
        NCM_ENABLED = "ncm_enabled"
        HOST = "host"
        PORT = "port"

    class PROJECT(IterableConstants):
        NAME = "name"

    class INIT_CONFIG(IterableConstants):
        CONFIG_FILE_LOCATION = "config_file_location"
        LOCAL_DIR_LOCATION = "local_dir_location"
        DB_LOCATION = "db_location"


class ENV_CONFIG:
    class CONNECTION(IterableConstants):
        CONNECTION_TIMEOUT = "CALM_DSL_CONNECTION_TIMEOUT"
        RETRIES_ENABLED = "CALM_DSL_RETRIES_ENABLED"
        READ_TIMEOUT = "CALM_DSL_READ_TIMEOUT"

    class LOG(IterableConstants):
        LEVEL = "CALM_DSL_LOG_LEVEL"

    class SERVER(IterableConstants):
        HOST = "CALM_DSL_PC_IP"
        PORT = "CALM_DSL_PC_PORT"
        USERNAME = "CALM_DSL_PC_USERNAME"
        PASSWORD = "CALM_DSL_PC_PASSWORD"

    class PROJECT(IterableConstants):
        NAME = "CALM_DSL_DEFAULT_PROJECT"

    class INIT_CONFIG:
        CONFIG_FILE_LOCATION = "CALM_DSL_CONFIG_FILE_LOCATION"
        LOCAL_DIR_LOCATION = "CALM_DSL_LOCAL_DIR_LOCATION"
        DB_LOCATION = "CALM_DSL_DB_LOCATION"

    COMPILE_SECRETS = "COMPILE_SECRETS"
