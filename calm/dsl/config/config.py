import os
import configparser
from jinja2 import Environment, PackageLoader

from .schema import validate_config
from .init_config import get_init_config_handle
from calm.dsl.tools import make_file_dir
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class ConfigFileParser:
    def __init__(self, config_file):

        config = configparser.ConfigParser()
        config.optionxform = str  # Maintaining case sensitivity for field names
        config.read(config_file)

        validate_config(config)

        config_obj = {}
        for section in config.sections():
            config_obj[section] = {}
            for k, v in config.items(section):
                config_obj[section][k] = v

        self._CONFIG = config_obj

    def get_server_config(self):
        """returns server config"""

        if "SERVER" in self._CONFIG:
            return self._CONFIG["SERVER"]

        else:
            return {}

    def get_project_config(self):
        """returns project config"""

        if "PROJECT" in self._CONFIG:
            return self._CONFIG["PROJECT"]

        else:
            return {}

    def get_log_config(self):
        """returns log config"""

        if "LOG" in self._CONFIG:
            return self._CONFIG["LOG"]

        else:
            return {}

    def get_categories_config(self):
        """returns categories config"""

        if "CATEGORIES" in self._CONFIG:
            return self._CONFIG["CATEGORIES"]

        else:
            return {}


class ConfigHandle:
    def __init__(self, config_file=None):

        if not config_file:
            init_config_handle = get_init_config_handle()
            init_obj = init_config_handle.get_init_data()
            config_file = init_obj["CONFIG"]["location"]

        config_obj = ConfigFileParser(config_file)

        self.server_config = config_obj.get_server_config()
        self.project_config = config_obj.get_project_config()
        self.log_config = config_obj.get_log_config()
        self.categories_config = config_obj.get_categories_config()

    def get_server_config(self):
        """returns server configuration"""

        return self.server_config

    def get_project_config(self):
        """returns project configuration"""

        return self.project_config

    def get_log_config(self):
        """returns logging configuration"""

        return self.log_config

    def get_categories_config(self):
        """returns config categories"""

        return self.categories_config

    @classmethod
    def get_init_config(cls):

        init_config_handle = get_init_config_handle()
        return init_config_handle.get_init_data()

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
    def update_config_file(
        cls, config_file, host, port, username, password, project_name, log_level
    ):
        """Updates the config file data"""

        LOG.debug("Rendering configuration template")
        make_file_dir(config_file)
        text = cls._render_config_template(
            host, port, username, password, project_name, log_level
        )

        LOG.debug("Writing configuration to '{}'".format(config_file))
        with open(config_file, "w") as fd:
            fd.write(text)


def get_config_handle(config_file=None):
    """returns ConfigHandle object"""

    return ConfigHandle(config_file)


def set_dsl_config(
    host,
    port,
    username,
    password,
    project_name,
    log_level,
    db_location,
    local_dir,
    config_file,
):

    """
    overrides the existing server/dsl configuration
    Note: This helper assumes that valid configuration is present. It is invoked just to update the existing configuration.

    if config_file is given, it will update config file location in `init.ini` and update the server details in that file

    Note: Context will not be changed according to it.
    """

    init_config_handle = get_init_config_handle()
    init_config_handle.update_init_config(
        config_file=config_file, db_file=db_location, local_dir=local_dir
    )

    ConfigHandle.update_config_file(
        config_file=config_file,
        host=host,
        port=port,
        username=username,
        password=password,
        project_name=project_name,
        log_level=log_level,
    )
