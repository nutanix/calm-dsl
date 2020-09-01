from .env_config import EnvConfig
from .config2 import ConfigHandle
from .init_config import InitConfig


class Context:
    _CONFIG_FILE = None

    _ConfigHandle = ConfigHandle
    _InitConfig = InitConfig

    def get_server_config(self):
        """
        # Priority (Decreases from 1 -> 3):
        # 1.) Config file passed as param
        # 2.) Environment Variables
        # 3.) Config file stored in init.ini
        """

        # Read data from default config file i.e. config file from init.ini
        config_obj = self._ConfigHandle()
        server_config = config_obj.get_server_config()

        # Updatiing by environment data
        env_config_data = EnvConfig.get_server_config()
        server_config["pc_ip"] = env_config_data["pc_ip"] or server_config["pc_ip"]
        server_config["pc_port"] = (
            env_config_data["pc_port"] or server_config["pc_port"]
        )
        server_config["pc_username"] = (
            env_config_data["pc_username"] or server_config["pc_username"]
        )
        server_config["pc_password"] = (
            env_config_data["pc_password"] or server_config["pc_password"]
        )

        # Updating by cli switch file (_CONFIG_FILE) if given
        if self._CONFIG_FILE:
            config_obj = self._ConfigHandle(self._CONFIG_FILE)
            config_file_data = config_obj.get_server_config()

            server_config["pc_ip"] = config_file_data["pc_ip"] or server_config["pc_ip"]
            server_config["pc_port"] = (
                config_file_data["pc_port"] or server_config["pc_port"]
            )
            server_config["pc_username"] = (
                config_file_data["pc_username"] or server_config["pc_username"]
            )
            server_config["pc_password"] = (
                config_file_data["pc_password"] or server_config["pc_password"]
            )

        return server_config

    def get_project_config(self):
        """returns project configuration"""

        # Read data from default config file i.e. config file from init.ini
        default_config_obj = self._ConfigHandle()
        project_config = default_config_obj.get_project_config()

        # Updating by cli switch file (_CONFIG_FILE) if given
        if self._CONFIG_FILE:
            config_obj = self._ConfigHandle(self._CONFIG_FILE)
            _project_config = config_obj.get_project_config()

            project_config["name"] = _project_config["name"] or project_config["name"]

        return project_config

    def get_log_config(self):
        """returns logging configuration"""

        # Read data from default config file i.e. config file from init.ini
        default_config_obj = self._ConfigHandle()
        log_config = default_config_obj.get_log_config()

        # Updating by cli switch file (_CONFIG_FILE) if given
        if self._CONFIG_FILE:
            config_obj = self._ConfigHandle(self._CONFIG_FILE)
            _log_config = config_obj.get_log_config()

            log_config["level"] = _log_config["level"] or log_config["level"]

        return log_config

    @classmethod
    def update_config_file_location(cls, config_file):
        """updates the config file location (global _CONFIG_FILE object)"""

        cls._CONFIG_FILE = config_file

    @classmethod
    def update_config_file(
        cls, host, port, username, password, project_name, log_level
    ):
        """updates config file data"""

        cls._ConfigHandle.update_config(
            host=host,
            port=port,
            username=username,
            password=password,
            project_name=project_name,
            log_level=log_level,
        )

    @classmethod
    def update_init_config_file(cls, config_file, db_file, local_dir):
        """updates the init file data"""

        cls._InitConfig.update_init_config(
            config_file=config_file, db_file=db_file, local_dir=local_dir
        )

    def set_config(
        self,
        host,
        port,
        username,
        password,
        project_name,
        db_location,
        log_level,
        local_dir,
        config_file,
    ):

        """
        overrides the existing server/dsl configuration
        Note: This helper assumes that valid configuration is present. It is invoked just to update the existing configuration.

        if config_file is given, it will update config file location in `init.ini` and update the server details in that file
        """

        # Missing data should be taken from existing configs.
        # Note: Passed config file will not be used at all to use missing data from

        server_config = self.get_server_config()
        host = host or server_config["pc_ip"]
        username = username or server_config["pc_username"]
        port = port or server_config["pc_port"]
        password = password or server_config["pc_password"]

        project_config = self.get_project_config()
        project_name = project_name or project_config.get("name") or "default"

        log_config = self.get_log_config()
        log_level = log_level or log_config.get("level") or "INFO"

        init_data = self._InitConfig.get_init_data()

        # TODO check pipelining of commands with changing db_location and local_dir should work
        # Updating init file data
        db_location = db_location or init_data["DB"]["location"]
        local_dir_location = local_dir or init_data["LOCAL_DIR"]["location"]
        config_file_location = config_file or init_data["CONFIG"]["location"]

        self.update_init_config_file(
            config_file=config_file_location,
            db_file=db_location,
            local_dir=local_dir_location,
        )

        # Updating config file data
        self.update_config_file(
            host=host,
            port=port,
            username=username,
            password=password,
            project_name=project_name,
            log_level=log_level,
        )

    def print_config(self):
        """prints the configuration"""

        server_config = self.get_server_config()
        project_config = self.get_project_config()
        log_config = self.get_log_config()

        config_str = self._ConfigHandle._render_config_template(
            ip=server_config["pc_ip"],
            port=server_config["pc_port"],
            username=server_config["pc_username"],
            password=server_config["pc_password"],
            project_name=project_config["name"],
            log_level=log_config["level"],
        )

        print(config_str)


def get_context():
    return Context()
