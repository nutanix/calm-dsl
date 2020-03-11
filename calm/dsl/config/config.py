import configparser
import errno
import os

from jinja2 import Environment, PackageLoader

from calm.dsl.tools import get_logging_handle

from .schema import validate_config, validate_init_config

LOG = get_logging_handle(__name__)


_CONFIG = None
_CONFIG_FILE = None
_INIT = None


def make_file_dir(config_file):
    """creates the file directory if not present"""

    # Create parent directory if not present
    if not os.path.exists(os.path.dirname(os.path.realpath(config_file))):
        try:
            LOG.debug("Creating directory for file {}".format(config_file))
            os.makedirs(os.path.dirname(os.path.realpath(config_file)))
            LOG.debug("Success")
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise Exception("[{}] - {}".format(exc["code"], exc["error"]))


def get_init_file_location():
    """returns the init file location"""

    init_file = os.path.join(os.path.expanduser("~"), ".calm", "init.ini")
    make_file_dir(init_file)
    return init_file


def get_default_config_file():
    """return default location of config file"""

    user_config_file = os.path.join(os.path.expanduser("~"), ".calm", "config.ini")
    make_file_dir(user_config_file)
    return user_config_file


def get_default_db_file():
    """return default location of db file"""

    dsl_db_file = os.path.join(os.path.expanduser("~"), ".calm", "dsl.db")
    make_file_dir(dsl_db_file)
    return dsl_db_file


def get_user_config_file():
    """returns the config file location"""

    global _CONFIG_FILE

    if not _CONFIG_FILE:
        init_obj = get_init_data()
        config_file = None
        if "CONFIG" in init_obj:
            config_file = init_obj["CONFIG"].get("location", None)

        _CONFIG_FILE = config_file or get_default_config_file()

    return _CONFIG_FILE


def get_init_data():
    """Returns the init config data"""

    global _INIT
    if not _INIT:
        update_init_obj()

    return _INIT


def update_init_obj():
    """updates the global init obj"""

    global _INIT
    config = configparser.ConfigParser()
    config.optionxform = str
    init_file = get_init_file_location()

    config.read(init_file)

    # Validate init config
    if not validate_init_config(config):
        raise ValueError("Invalid init config file: {}".format(init_file))

    _INIT = config


def update_init_config(config_file, db_file, local_dir):
    """updates the init file data"""

    global _CONFIG_FILE

    init_file = get_init_file_location()
    LOG.debug("Rendering init template")
    text = _render_init_template(config_file, db_file, local_dir)
    LOG.debug("Success")

    # UPDATE global _CONFIG_FILE object
    _CONFIG_FILE = config_file

    init_obj = get_init_data()
    config_file = config_file or init_obj["CONFIG"]["location"]

    db_file = db_file or init_obj["DB"]["location"]

    local_dir = local_dir or init_obj["LOCAL_DIR"]["location "]

    # Write config
    LOG.debug("Writing configuration to '{}'".format(init_file))
    with open(init_file, "w") as fd:
        fd.write(text)
    LOG.debug("Success")

    # Update existing init object
    update_init_obj()


def _render_init_template(
    config_file, db_file, local_dir, schema_file="init.ini.jinja2"
):
    """renders the init template"""

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)
    text = template.render(
        config_file=config_file, db_file=db_file, local_dir=local_dir,
    )
    return text.strip() + os.linesep


def _render_config_template(
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


def _get_config_file():
    """returns the location of config file present in user location /cwd / default config file """

    global _CONFIG_FILE
    cwd = os.getcwd()

    if _CONFIG_FILE:
        user_config_file = _CONFIG_FILE

    elif "config.ini" in os.listdir(cwd):
        user_config_file = os.path.join(cwd, "config.ini")

    else:
        user_config_file = get_user_config_file()

    # create a config file
    make_file_dir(user_config_file)

    return user_config_file


def init_config(
    ip, port, username, password, project_name, log_level, config_file=None
):
    """Writes the configuration to config file / default config file"""

    # Default user config file
    user_config_file = _get_config_file()
    config_file = config_file or user_config_file

    # Render config template
    LOG.debug("Rendering configuration template")
    text = _render_config_template(
        ip, port, username, password, project_name, log_level
    )
    LOG.debug("Success")

    # Write config
    LOG.debug("Writing configuration to '{}'".format(config_file))
    with open(config_file, "w") as fd:
        fd.write(text)
    LOG.debug("Success")


def get_config(config_file=None):
    """return the config object"""

    global _CONFIG, _CONFIG_FILE

    if config_file:
        _CONFIG_FILE = config_file

    if (not _CONFIG) or (config_file):
        # Create config object
        user_config_file = _get_config_file()
        config = configparser.ConfigParser()
        config.optionxform = str  # Maintaining case sensitivity for field names
        config.read(user_config_file)

        # Validate config
        if not validate_config(config):
            raise ValueError("Invalid config file: {}".format(user_config_file))

        _CONFIG = config

    return _CONFIG


def set_config(
    host,
    port,
    username,
    password,
    project_name,
    db_location,
    log_level,
    config_file,
    local_dir,
):
    """writes the configuration to config file"""

    config = get_config()
    init_obj = get_init_data()

    host = host or config["SERVER"]["pc_ip"]
    username = username or config["SERVER"]["pc_username"]
    port = port or config["SERVER"]["pc_port"]
    password = password or config["SERVER"]["pc_password"]
    project_name = project_name or config["PROJECT"]["name"]
    log_level = log_level or config["LOG"]["level"]

    logging_levels = LOG.get_logging_levels()
    if log_level not in logging_levels:
        raise ValueError("Invalid log level. Select from {}".format(logging_levels))

    make_file_dir(config_file)
    init_config(
        host,
        port,
        username,
        password,
        project_name,
        log_level,
        config_file=config_file,
    )

    db_location = db_location or init_obj["DB"]["location"]
    local_dir = local_dir or init_obj["LOCAL_DIR"]["location"]
    config_file = config_file or init_obj["CONFIG"]["location"]

    # Update init config
    update_init_config(
        config_file=config_file, db_file=db_location, local_dir=local_dir
    )


def print_config():
    """prints the configuration"""

    config_file = _get_config_file()
    LOG.debug("Fetching configuration from '{}'".format(config_file))
    print("")
    with open(config_file) as fd:
        print(fd.read())
