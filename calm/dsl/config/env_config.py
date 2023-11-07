import os

from .constants import ENV_CONFIG, CONFIG


class EnvConfig:
    pc_ip = os.environ.get(ENV_CONFIG.SERVER.HOST) or ""
    pc_port = os.environ.get(ENV_CONFIG.SERVER.PORT) or ""
    pc_username = os.environ.get(ENV_CONFIG.SERVER.USERNAME) or ""
    pc_password = os.environ.get(ENV_CONFIG.SERVER.PASSWORD) or ""
    default_project = os.environ.get(ENV_CONFIG.PROJECT.NAME) or ""
    log_level = os.environ.get(ENV_CONFIG.LOG.LEVEL) or ""

    config_file_location = (
        os.environ.get(ENV_CONFIG.INIT_CONFIG.CONFIG_FILE_LOCATION) or ""
    )
    local_dir_location = os.environ.get(ENV_CONFIG.INIT_CONFIG.LOCAL_DIR_LOCATION) or ""
    db_location = os.environ.get(ENV_CONFIG.INIT_CONFIG.DB_LOCATION)
    is_compile_secrets = os.environ.get(ENV_CONFIG.COMPILE_SECRETS) or "false"

    connection_timeout = os.environ.get(ENV_CONFIG.CONNECTION.CONNECTION_TIMEOUT) or ""
    read_timeout = os.environ.get(ENV_CONFIG.CONNECTION.READ_TIMEOUT) or ""
    retries_enabled = os.environ.get(ENV_CONFIG.CONNECTION.RETRIES_ENABLED) or ""

    @classmethod
    def is_compile_secret(cls):
        return cls.is_compile_secrets.lower() == "true"

    @classmethod
    def get_server_config(cls):

        config = {}
        if cls.pc_ip:
            config[CONFIG.SERVER.HOST] = cls.pc_ip

        if cls.pc_port:
            config[CONFIG.SERVER.PORT] = cls.pc_port

        if cls.pc_username:
            config[CONFIG.SERVER.USERNAME] = cls.pc_username

        if cls.pc_password:
            config[CONFIG.SERVER.PASSWORD] = cls.pc_password

        return config

    @classmethod
    def get_project_config(cls):

        config = {}
        if cls.default_project:
            config[CONFIG.PROJECT.NAME] = cls.default_project

        return config

    @classmethod
    def get_log_config(cls):

        config = {}
        if cls.log_level:
            config[CONFIG.LOG.LEVEL] = cls.log_level

        return config

    @classmethod
    def get_init_config(cls):

        config = {}
        if cls.config_file_location:
            config[CONFIG.INIT_CONFIG.CONFIG_FILE_LOCATION] = cls.config_file_location

        if cls.local_dir_location:
            config[CONFIG.INIT_CONFIG.LOCAL_DIR_LOCATION] = cls.local_dir_location

        if cls.db_location:
            config[CONFIG.INIT_CONFIG.DB_LOCATION] = cls.db_location

        return config

    @classmethod
    def get_connection_config(cls):

        config = {}
        if cls.connection_timeout:
            config[CONFIG.CONNECTION.CONNECTION_TIMEOUT] = int(cls.connection_timeout)

        if cls.read_timeout:
            config[CONFIG.CONNECTION.READ_TIMEOUT] = int(cls.read_timeout)

        if cls.retries_enabled:
            config[CONFIG.CONNECTION.RETRIES_ENABLED] = (
                cls.retries_enabled.lower() == "true"
            )

        return config
