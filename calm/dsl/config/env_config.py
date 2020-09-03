import os


class EnvConfig:
    pc_ip = os.environ.get("PC_IP") or ""
    pc_port = os.environ.get("PC_PORT") or ""
    pc_username = os.environ.get("PC_USERNAME") or ""
    pc_password = os.environ.get("PC_PASSWORD") or ""
    default_project = os.environ.get("DSL_DEFAULT_PROJECT") or ""
    log_level = os.environ.get("DSL_LOG_LEVEL") or ""

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
