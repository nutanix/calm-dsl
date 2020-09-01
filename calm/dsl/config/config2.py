import os
import configparser
from jinja2 import Environment, PackageLoader

from .schema import validate_init_config, validate_config
from .init_config import InitConfig
from .utils import make_file_dir
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class ConfigHandle:
    _CONFIG_FILE = None

    def __init__(self, config_file=None):

        if not config_file:
            init_obj = InitConfig.get_init_data()
            config_file = init_obj["CONFIG"]["location"]

        self._CONFIG_FILE = config_file

        config = configparser.ConfigParser()
        config.optionxform = str  # Maintaining case sensitivity for field names
        config.read(config_file)

        validate_config(config)
        self._CONFIG = config

    # Note: It is a classmethod, because it requires atleast a location to read config from
    def get_server_config(self):

        if "SERVER" not in self._CONFIG:
            return {"pc_ip": "", "pc_port": "", "pc_username": "", "pc_password": ""}

        else:
            c_data = self._CONFIG["SERVER"]
            return {
                "pc_ip": c_data.get("pc_ip") or "",
                "pc_port": c_data.get("pc_port") or "",
                "pc_username": c_data.get("pc_username") or "",
                "pc_password": c_data.get("pc_password") or "",
            }

    def get_project_config(self):

        if "PROJECT" not in self._CONFIG:
            return {"name": ""}

        else:
            return {"name": self._CONFIG["PROJECT"].get("name") or ""}

    def get_log_config(self):

        if "LOG" not in self._CONFIG:
            return {"level": ""}

        else:
            return {"level": self._CONFIG["LOG"].get("level") or ""}

    @classmethod
    def _render_config_template(
        cls,
        ip,
        port,
        username,
        password,
        project_name,
        log_level,
        schema_file="config.ini.jinja2",
    ):
        """renders the config template"""

        loader = PackageLoader(__name__, "")
        env = Environment(loader=loader)
        template = env.get_template(schema_file)
        text = template.render(
            ip=ip,
            port=port,
            username=username,
            password=password,
            project_name=project_name,
            log_level=log_level,
        )
        return text.strip() + os.linesep

    @classmethod
    def update_config(cls, host, port, username, password, project_name, log_level):
        """Updates the config file data"""

        config_file = cls._CONFIG_FILE
        if not config_file:
            init_obj = InitConfig.get_init_data()
            config_file = init_obj["CONFIG"]["location"]

        LOG.debug("Rendering configuration template")
        make_file_dir(config_file)
        text = cls._render_config_template(
            host, port, username, password, project_name, log_level
        )

        LOG.debug("Writing configuration to '{}'".format(config_file))
        with open(config_file, "w") as fd:
            fd.write(text)
