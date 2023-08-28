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

        config = configparser.RawConfigParser()
        config.optionxform = str  # Maintaining case sensitivity for field names
        config.read(config_file)

        validate_config(config)

        config_obj = {}
        for section in config.sections():
            config_obj[section] = {}
            for k, v in config.items(section):
                config_obj[section][k] = v

        self._CONFIG = config_obj
        self._CONFIG_PARSER_OBJECT = config

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

    def get_policy_config(self):
        """returns policy config"""

        if "POLICY" in self._CONFIG:
            return self._CONFIG["POLICY"]

        else:
            return {}

    def get_approval_policy_config(self):
        """returns approval policy config"""

        if "APPROVAL_POLICY" in self._CONFIG:
            return self._CONFIG["APPROVAL_POLICY"]

        else:
            return {}

    def get_stratos_config(self):
        """returns stratos config"""

        stratos_config = {}
        if "STRATOS" in self._CONFIG_PARSER_OBJECT:
            for k, v in self._CONFIG_PARSER_OBJECT.items("STRATOS"):
                if k == "stratos_status":
                    stratos_config[k] = self._CONFIG_PARSER_OBJECT[
                        "STRATOS"
                    ].getboolean(k)
                else:
                    stratos_config[k] = v

        return stratos_config

    def get_categories_config(self):
        """returns categories config"""

        if "CATEGORIES" in self._CONFIG:
            return self._CONFIG["CATEGORIES"]

        else:
            return {}

    def get_connection_config(self):
        """returns connection config"""

        connection_config = {}
        if "CONNECTION" in self._CONFIG_PARSER_OBJECT:
            for k, v in self._CONFIG_PARSER_OBJECT.items("CONNECTION"):
                if k == "retries_enabled":
                    connection_config[k] = self._CONFIG_PARSER_OBJECT[
                        "CONNECTION"
                    ].getboolean(k)
                elif k in ["connection_timeout", "read_timeout"]:
                    connection_config[k] = self._CONFIG_PARSER_OBJECT[
                        "CONNECTION"
                    ].getint(k)
                else:
                    connection_config[k] = v

        return connection_config


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
        self.policy_config = config_obj.get_policy_config()
        self.approval_policy_config = config_obj.get_approval_policy_config()
        self.stratos_config = config_obj.get_stratos_config()
        self.categories_config = config_obj.get_categories_config()
        self.connection_config = config_obj.get_connection_config()

    def get_server_config(self):
        """returns server configuration"""

        return self.server_config

    def get_project_config(self):
        """returns project configuration"""

        return self.project_config

    def get_log_config(self):
        """returns logging configuration"""

        return self.log_config

    def get_policy_config(self):
        """returns policy status"""
        return self.policy_config

    def get_approval_policy_config(self):
        """returns approval policy status"""
        return self.approval_policy_config

    def get_stratos_config(self):
        """returns approval policy status"""
        return self.stratos_config

    def get_categories_config(self):
        """returns config categories"""

        return self.categories_config

    def get_connection_config(self):
        """returns connection config"""

        return self.connection_config

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
        retries_enabled,
        connection_timeout,
        read_timeout,
        policy_status,
        approval_policy_status,
        stratos_status,
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
            retries_enabled=retries_enabled,
            connection_timeout=connection_timeout,
            read_timeout=read_timeout,
            policy_status=policy_status,
            approval_policy_status=approval_policy_status,
            stratos_status=stratos_status,
        )
        return text.strip() + os.linesep

    @classmethod
    def update_config_file(
        cls,
        config_file,
        host,
        port,
        username,
        password,
        project_name,
        log_level,
        retries_enabled,
        connection_timeout,
        read_timeout,
        policy_status,
        approval_policy_status,
        stratos_status,
    ):
        """Updates the config file data"""

        LOG.debug("Rendering configuration template")
        make_file_dir(config_file)
        text = cls._render_config_template(
            host,
            port,
            username,
            password,
            project_name,
            log_level,
            retries_enabled,
            connection_timeout,
            read_timeout,
            policy_status,
            approval_policy_status,
            stratos_status,
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
    retries_enabled,
    connection_timeout,
    read_timeout,
    policy_status,
    approval_policy_status,
    stratos_status,
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
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
        policy_status=policy_status,
        approval_policy_status=approval_policy_status,
        stratos_status=stratos_status,
    )
