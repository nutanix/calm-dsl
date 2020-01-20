import os
import errno
import configparser

from jinja2 import Environment, PackageLoader

from .config_schema import validate_config
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


_CONFIG = None


def make_config_file_dir(config_file):
    """creates the config file directory if not present"""

    # Create parent directory if not present
    if not os.path.exists(os.path.dirname(os.path.realpath(config_file))):
        try:
            LOG.debug("Creating directory for file {}".format(config_file))
            os.makedirs(os.path.dirname(os.path.realpath(config_file)))
            LOG.debug("Success")
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise Exception("[{}] - {}".format(exc["code"], exc["error"]))


def get_default_user_config_file():

    user_config_file = os.path.join(os.path.expanduser("~"), ".calm", "config.ini")
    make_config_file_dir(user_config_file)
    return user_config_file


def _render_config_template(
    ip,
    port,
    username,
    password,
    project_name,
    db_location,
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
        db_location=db_location,
    )
    return text.strip() + os.linesep


def _get_config_file():
    """returns the location of config file present in cwd / default config file """

    cwd = os.getcwd()
    if "config.ini" in os.listdir(cwd):
        user_config_file = os.path.join(cwd, "config.ini")

    else:
        user_config_file = get_default_user_config_file()
        if not os.path.exists(user_config_file):
            raise Exception(
                "Config file {} not found. Please run: calm init dsl".format(
                    user_config_file
                )
            )

    return user_config_file


def init_config(
    ip, port, username, password, project_name, db_location, config_file=None
):
    """Writes the configuration to config file / default config file"""

    # Default user config file
    user_config_file = get_default_user_config_file()
    config_file = config_file or user_config_file

    # Render config template
    LOG.debug("Rendering configuration template ...")
    text = _render_config_template(
        ip, port, username, password, project_name, db_location
    )
    LOG.debug("Success")

    # Write config
    LOG.debug("Writing configuration to '{}' ...".format(config_file))
    with open(config_file, "w") as fd:
        fd.write(text)
    LOG.debug("Success")


def get_config():
    """return the config object"""

    global _CONFIG

    if not _CONFIG:
        # Create config object
        user_config_file = _get_config_file()
        config = configparser.ConfigParser()
        config.optionxform = str  # Maintaining case sensitivity for field names
        config.read(user_config_file)

        # Validate config
        if not validate_config(config):
            raise Exception("Invalid config file: {}".format(user_config_file))

        _CONFIG = config

    return _CONFIG


def set_config(host, port, username, password, project_name, db_location, config_file):
    """writes the configuration to config file"""

    config = get_config()

    host = host or config["SERVER"]["pc_ip"]
    username = username or config["SERVER"]["pc_username"]
    port = port or config["SERVER"]["pc_port"]
    password = password or config["SERVER"]["pc_password"]
    project_name = project_name or config["PROJECT"]["name"]
    db_location = db_location or config["DB"]["location"]

    make_config_file_dir(config_file)
    init_config(
        host,
        port,
        username,
        password,
        project_name,
        db_location,
        config_file=config_file,
    )


def print_config():
    """prints the configuration"""

    config_file = _get_config_file()
    LOG.debug("Fetching configuration from '{}'".format(config_file))
    print("")
    with open(config_file) as fd:
        print(fd.read())
