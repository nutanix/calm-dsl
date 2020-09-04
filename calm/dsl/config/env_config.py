import os


class EnvConfig:
    pc_ip = os.environ.get("CALM_DSL_PC_IP") or ""
    pc_port = os.environ.get("CALM_DSL_PC_PORT") or ""
    pc_username = os.environ.get("CALM_DSL_PC_USERNAME") or ""
    pc_password = os.environ.get("CALM_DSL_PC_PASSWORD") or ""
    default_project = os.environ.get("CALM_DSL_DEFAULT_PROJECT") or ""
    log_level = os.environ.get("CALM_DSL_LOG_LEVEL") or ""

    config_file_location = os.environ.get("CALM_DSL_CONFIG_FILE_LOCATION") or ""
    local_dir_location = os.environ.get("CALM_DSL_LOCAL_DIR_LOCATION") or ""
    db_location = os.environ.get("CALM_DSL_DB_LOCATION")

    @classmethod
    def get_server_config(cls):

        config = {}
        if cls.pc_ip:
            config["pc_ip"] = cls.pc_ip

        if cls.pc_port:
            config["pc_port"] = cls.pc_port

        if cls.pc_username:
            config["pc_username"] = cls.pc_username

        if cls.pc_password:
            config["pc_password"] = cls.pc_password

        return config

    @classmethod
    def get_project_config(cls):

        config = {}
        if cls.default_project:
            config["name"] = cls.default_project

        return config

    @classmethod
    def get_log_config(cls):

        config = {}
        if cls.log_level:
            config["level"] = cls.log_level

        return config

    @classmethod
    def get_init_config(cls):

        config = {}
        if cls.config_file_location:
            config["config_file_location"] = cls.config_file_location

        if cls.local_dir_location:
            config["local_dir_location"] = cls.local_dir_location

        if cls.db_location:
            config["db_location"] = cls.db_location

        return config
