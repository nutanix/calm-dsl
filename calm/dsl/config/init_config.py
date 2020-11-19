import os
import configparser
from jinja2 import Environment, PackageLoader

from .schema import validate_init_config
from .env_config import EnvConfig
from calm.dsl.tools import make_file_dir
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

INIT_FILE_LOCATION = os.path.join(os.path.expanduser("~"), ".calm", "init.ini")
DEFAULT_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".calm", "config.ini")
DEFAULT_DB_LOCATION = os.path.join(os.path.expanduser("~"), ".calm", "dsl.db")
DEFAULT_LOCAL_DIR_LOCATION = os.path.join(os.path.expanduser("~"), ".calm", ".local")


class InitConfigHandle:
    def __init__(self):

        init_file = INIT_FILE_LOCATION
        init_config = configparser.ConfigParser()
        init_config.optionxform = str
        init_config.read(init_file)

        # Validate init config
        if not validate_init_config(init_config):
            raise ValueError(
                "Invalid init config file: {}. Please run: calm init dsl".format(
                    init_file
                )
            )

        config_obj = {}
        for section in init_config.sections():
            config_obj[section] = {}
            for k, v in init_config.items(section):
                config_obj[section][k] = v

        env_init_config = EnvConfig.get_init_config()

        if not config_obj.get("CONFIG", {}).get("location"):
            make_file_dir(DEFAULT_CONFIG_FILE)
            config_obj["CONFIG"] = {"location": DEFAULT_CONFIG_FILE}

        if env_init_config.get("config_file_location"):
            config_obj["CONFIG"]["LOCATION"] = env_init_config["config_file_location"]

        if not config_obj.get("DB", {}).get("location"):
            make_file_dir(DEFAULT_DB_LOCATION)
            config_obj["DB"] = {"location": DEFAULT_DB_LOCATION}

        if env_init_config.get("db_location"):
            config_obj["DB"]["LOCATION"] = env_init_config["db_location"]

        if not config_obj.get("LOCAL_DIR", {}).get("location"):
            make_file_dir(DEFAULT_LOCAL_DIR_LOCATION)
            config_obj["LOCAL_DIR"] = {"location": DEFAULT_LOCAL_DIR_LOCATION}

        if env_init_config.get("local_dir_location"):
            config_obj["LOCAL_DIR"]["LOCATION"] = env_init_config["local_dir_location"]

        self._CONFIG = config_obj

    def get_init_data(self):

        return self._CONFIG

    @classmethod
    def update_init_config(cls, config_file, db_file, local_dir):
        """updates the init file data"""

        # create required directories
        make_file_dir(config_file)
        make_file_dir(db_file)
        make_file_dir(local_dir, is_dir=True)

        # Note: No need to validate init data as it is rendered by template
        init_file = INIT_FILE_LOCATION
        make_file_dir(init_file)

        LOG.debug("Rendering init template")
        text = cls._render_init_template(config_file, db_file, local_dir)

        # Write init configuration
        LOG.debug("Writing configuration to '{}'".format(init_file))
        with open(init_file, "w") as fd:
            fd.write(text)

    @staticmethod
    def _render_init_template(
        config_file, db_file, local_dir, schema_file="init.ini.jinja2"
    ):
        """renders the init template"""

        loader = PackageLoader(__name__, "")
        env = Environment(loader=loader)
        template = env.get_template(schema_file)
        text = template.render(
            config_file=config_file, db_file=db_file, local_dir=local_dir
        )
        return text.strip() + os.linesep


_INIT_CONFIG_HANDLE = None


def get_init_config_handle():

    global _INIT_CONFIG_HANDLE
    if not _INIT_CONFIG_HANDLE:
        _INIT_CONFIG_HANDLE = InitConfigHandle()

    return _INIT_CONFIG_HANDLE


def get_default_config_file():
    """Returns default location of config file"""

    return DEFAULT_CONFIG_FILE


def get_default_db_file():
    """Returns default location of db file"""

    return DEFAULT_DB_LOCATION


def get_default_local_dir():
    """Returns the default location for local dir"""

    return DEFAULT_LOCAL_DIR_LOCATION
