import os
import sys

from .env_config import EnvConfig
from .config import get_config_handle
from .constants import CONFIG
from calm.dsl.log import get_logging_handle
from calm.dsl.constants import DSL_CONFIG

LOG = get_logging_handle(__name__)

DEFAULT_RETRIES_ENABLED = True
DEFAULT_CONNECTION_TIMEOUT = 5
DEFAULT_READ_TIMEOUT = 30
DEFAULT_LOG_LEVEL = "INFO"


class Context:
    def __init__(self):

        self.initialize_configuration()

    def initialize_configuration(self):
        """initializes the confguration for context
        Priority (Decreases from 1 -> 3):
        1.) Config file passed as param
        2.) Environment Variables
        3.) Config file stored in init.ini
        """

        config_handle = get_config_handle()
        self.server_config = config_handle.get_server_config()
        self.ncm_server_config = config_handle.get_ncm_server_config()
        self.project_config = config_handle.get_project_config()
        self.log_config = config_handle.get_log_config()
        self.categories_config = config_handle.get_categories_config()
        self.policy_config = config_handle.get_policy_config()
        self.approval_policy_config = config_handle.get_approval_policy_config()
        self.stratos_config = config_handle.get_stratos_config()
        self.cp_config = config_handle.get_cp_config()
        self.connection_config = config_handle.get_connection_config()
        # Override with env data
        self.server_config.update(EnvConfig.get_server_config())
        self.project_config.update(EnvConfig.get_project_config())
        self.log_config.update(EnvConfig.get_log_config())
        self.connection_config.update(EnvConfig.get_connection_config())

        init_config = config_handle.get_init_config()
        self._CONFIG_FILE = init_config["CONFIG"]["location"]
        self._PROJECT = self.project_config.get("name", "")

    def reset_configuration(self):
        """Resets the configuration"""

        LOG.debug("Resetting configuration in dsl context")
        self.initialize_configuration()

    def validate_init_config(self):
        """validates the init config"""

        config_handle = get_config_handle()
        init_config = config_handle.get_init_config()

        if self._CONFIG_FILE == init_config["CONFIG"]["location"]:
            if not os.path.exists(self._CONFIG_FILE):
                LOG.error("Invalid config file location '{}'".format(self._CONFIG_FILE))
                sys.exit(-1)

    def get_server_config(self):
        """returns server configuration"""

        config = self.server_config
        try:  # if all server variables are present either in env or some other way, not required to validate config file
            if not config.get(CONFIG.SERVER.HOST):
                LOG.error(
                    "Host IP not found. Please provide it in config file or set environment variable 'CALM_DSL_PC_IP'"
                )
                sys.exit(-1)

            if not config.get(CONFIG.SERVER.PORT):
                LOG.error(
                    "Host Port not found. Please provide it in config file or set environment variable 'CALM_DSL_PC_PORT'"
                )
                sys.exit(-1)

            if not config.get(CONFIG.SERVER.USERNAME):
                LOG.error(
                    "Host username not found. Please provide it in config file or set environment variable 'CALM_DSL_PC_USERNAME'"
                )
                sys.exit(-1)

            if not config.get(CONFIG.SERVER.PASSWORD):
                LOG.error(
                    "Host password not found. Please provide it in config file or set environment variable 'CALM_DSL_PC_PASSWORD'"
                )
                sys.exit(-1)

        except:  # validate init_config file, if it's contents are valid
            self.validate_init_config()
            raise

        return config

    def get_ncm_server_config(self):
        """returns NCM server configuration"""
        config = self.ncm_server_config
        if not config.get(CONFIG.NCM_SERVER.NCM_ENABLED):
            config[CONFIG.NCM_SERVER.NCM_ENABLED] = False

        return config

    def get_project_config(self):
        """returns project configuration"""

        config = self.project_config
        if not config.get(CONFIG.PROJECT.NAME):
            config["name"] = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME

        return config

    def get_connection_config(self):
        """returns connection configuration"""

        config = self.connection_config
        default_configuration = get_default_connection_config()
        for _key in CONFIG.CONNECTION.ALL():
            if _key not in config:
                config[_key] = default_configuration[_key]

        return config

    def get_policy_config(self):
        """returns policy configuration"""
        config = self.policy_config
        if not config.get(CONFIG.POLICY.STATUS):
            config[CONFIG.POLICY.STATUS] = False

        return config

    def get_approval_policy_config(self):
        """returns approval policy configuration"""
        config = self.approval_policy_config
        if not config.get(CONFIG.APPROVAL_POLICY.STATUS):
            config[CONFIG.APPROVAL_POLICY.STATUS] = False

        return config

    def get_stratos_config(self):
        """returns stratos configuration"""
        config = self.stratos_config
        if not config.get(CONFIG.STRATOS.STATUS):
            config[CONFIG.STRATOS.STATUS] = False

        return config

    def get_cp_config(self):
        """returns custom-provider configuration"""
        config = self.cp_config
        if not config.get(CONFIG.CLOUD_PROVIDERS.STATUS):
            config[CONFIG.CLOUD_PROVIDERS.STATUS] = False

        return config

    def get_log_config(self):
        """returns logging configuration"""

        config = self.log_config
        default_configuration = get_default_log_config()
        if not config.get(CONFIG.LOG.LEVEL):
            LOG.warning(
                "Default log-level not found in config file or environment('CALM_DSL_LOG_LEVEL'). Setting it to 'INFO' level"
            )
            config["level"] = default_configuration["level"]

        return config

    def get_categories_config(self):
        """returns config categories"""

        return self.categories_config

    def get_init_config(self):
        """returns init configuration"""

        config_handle = get_config_handle()
        return config_handle.get_init_config()

    def update_project_context(self, project_name):
        """Overrides the existing project configuration"""

        self._PROJECT = project_name
        LOG.debug("Updating project in dsl context to {}".format(project_name))
        self.project_config["name"] = project_name

    def update_ncm_server_context(self, ncm_enabled, host, port):
        """Overrides the existing NCM server configuration"""

        LOG.debug(
            "Updating NCM server in dsl context to {}, {}, {}".format(
                ncm_enabled, host, port
            )
        )
        self.ncm_server_config.update(
            {
                CONFIG.NCM_SERVER.NCM_ENABLED: ncm_enabled,
                CONFIG.NCM_SERVER.HOST: host,
                CONFIG.NCM_SERVER.PORT: port,
            }
        )

    def update_config_file_context(self, config_file):
        """Overrides the existing configuration with passed file configuration"""

        LOG.debug("Updating config file in dsl context to {}".format(config_file))
        self._CONFIG_FILE = config_file
        cxt_config_handle = get_config_handle(self._CONFIG_FILE)
        self.server_config.update(cxt_config_handle.get_server_config())
        self.ncm_server_config.update(cxt_config_handle.get_ncm_server_config())
        self.project_config.update(cxt_config_handle.get_project_config())
        self.log_config.update(cxt_config_handle.get_log_config())
        self.connection_config.update(cxt_config_handle.get_connection_config())

        if cxt_config_handle.get_categories_config():
            self.categories_config = cxt_config_handle.get_categories_config()

    def print_config(self):
        """prints the configuration"""

        server_config = self.get_server_config()
        ncm_server_config = self.get_ncm_server_config()
        project_config = self.get_project_config()
        log_config = self.get_log_config()
        policy_config = self.get_policy_config()
        approval_policy_config = self.get_approval_policy_config()
        stratos_status = self.get_stratos_config()
        cp_status = self.get_cp_config()
        connection_config = self.get_connection_config()

        ConfigHandle = get_config_handle()
        config_str = ConfigHandle._render_config_template(
            ip=server_config[CONFIG.SERVER.HOST],
            port=server_config[CONFIG.SERVER.PORT],
            username=server_config[CONFIG.SERVER.USERNAME],
            password="xxxxxxxx",  # Do not render password
            ncm_enabled=ncm_server_config[CONFIG.NCM_SERVER.NCM_ENABLED],
            ncm_host=ncm_server_config.get(
                CONFIG.NCM_SERVER.HOST, DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
            ),
            ncm_port=ncm_server_config.get(
                CONFIG.NCM_SERVER.PORT, DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
            ),
            api_key_location=server_config.get(
                CONFIG.SERVER.API_KEY_LOCATION, DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
            ),
            project_name=project_config[CONFIG.PROJECT.NAME],
            log_level=log_config[CONFIG.LOG.LEVEL],
            policy_status=policy_config[CONFIG.POLICY.STATUS],
            approval_policy_status=approval_policy_config[
                CONFIG.APPROVAL_POLICY.STATUS
            ],
            stratos_status=stratos_status[CONFIG.STRATOS.STATUS],
            retries_enabled=connection_config[CONFIG.CONNECTION.RETRIES_ENABLED],
            connection_timeout=connection_config[CONFIG.CONNECTION.CONNECTION_TIMEOUT],
            read_timeout=connection_config[CONFIG.CONNECTION.READ_TIMEOUT],
            cp_status=cp_status[CONFIG.CLOUD_PROVIDERS.STATUS],
        )

        print(config_str)


_ContextHandle = None


def init_context():

    global _ContextHandle
    _ContextHandle = Context()


def get_context():
    global _ContextHandle
    if not _ContextHandle:
        init_context()

    return _ContextHandle


def get_default_connection_config():
    """Returns default connection config"""

    return {
        "connection_timeout": DEFAULT_CONNECTION_TIMEOUT,
        "read_timeout": DEFAULT_READ_TIMEOUT,
        "retries_enabled": DEFAULT_RETRIES_ENABLED,
    }


def get_default_log_config():
    """Returns default log config"""

    return {"level": DEFAULT_LOG_LEVEL}
