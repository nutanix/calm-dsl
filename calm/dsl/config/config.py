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


def make_file_dir(path, is_dir=False):
    """creates the file directory if not present"""

    # Create parent directory if not present
    if not os.path.exists(os.path.dirname(os.path.realpath(path))):
        try:
            LOG.debug("Creating directory for file {}".format(path))
            os.makedirs(os.path.dirname(os.path.realpath(path)))

        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise Exception("[{}] - {}".format(exc["code"], exc["error"]))

    if is_dir and (not os.path.exists(path)):
        os.makedirs(path)


def get_init_file():
    """Returns the init file location"""

    init_file = os.path.join(os.path.expanduser("~"), ".calm", "init.ini")
    make_file_dir(init_file)
    return init_file


def get_default_config_file():
    """Returns default location of config file"""

    user_config_file = os.path.join(os.path.expanduser("~"), ".calm", "config.ini")
    make_file_dir(user_config_file)
    return user_config_file


def get_default_db_file():
    """Returns default location of db file"""

    dsl_db_file = os.path.join(os.path.expanduser("~"), ".calm", "dsl.db")
    make_file_dir(dsl_db_file)
    return dsl_db_file


def get_default_local_dir():
    """Returns the default location for local dir"""

    local_dir = os.path.join(os.path.expanduser("~"), ".calm", ".local")
    make_file_dir(local_dir, is_dir=True)
    return local_dir


def get_user_config_file():
    """Returns the config file location"""

    global _CONFIG_FILE
    cwd = os.getcwd()

    if not _CONFIG_FILE:

        config_file = None
        if "config.ini" in os.listdir(cwd):
            config_file = os.path.join(cwd, "config.ini")

        elif os.path.exists(get_init_file()):
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
    init_file = get_init_file()

    config.read(init_file)

    # Validate init config
    if not validate_init_config(config):
        raise ValueError(
            "Invalid init config file: {}.  Please run: calm init dsl".format(init_file)
        )

    _INIT = config


def update_init_config(config_file, db_file, local_dir):
    """updates the init file data"""

    global _CONFIG_FILE

    # create required directories
    make_file_dir(config_file)
    make_file_dir(db_file)
    make_file_dir(local_dir, is_dir=True)

    init_file = get_init_file()
    LOG.debug("Rendering init template")
    text = _render_init_template(config_file, db_file, local_dir)

    # UPDATE global _CONFIG_FILE object
    _CONFIG_FILE = config_file

    # Write config
    LOG.debug("Writing configuration to '{}'".format(init_file))
    with open(init_file, "w") as fd:
        fd.write(text)

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


def init_config(
    ip, port, username, password, project_name, log_level, config_file=None
):
    """Writes the configuration to config file / default config file"""

    # Default user config file
    user_config_file = get_user_config_file()
    config_file = config_file or user_config_file

    # Render config template
    LOG.debug("Rendering configuration template")
    text = _render_config_template(
        ip, port, username, password, project_name, log_level
    )

    # Write config
    LOG.debug("Writing configuration to '{}'".format(config_file))
    with open(config_file, "w") as fd:
        fd.write(text)


def get_config(config_file=None):
    """Returns the config object"""

    global _CONFIG, _CONFIG_FILE

    if config_file:
        _CONFIG_FILE = config_file

    if (not _CONFIG) or (config_file):
        # Create config object
        user_config_file = get_user_config_file()
        config = configparser.ConfigParser()
        config.optionxform = str  # Maintaining case sensitivity for field names
        config.read(user_config_file)

        # Check presence of file
        if not os.path.exists(user_config_file):
            raise FileNotFoundError(
                "File {} not found. Please run: calm init dsl".format(user_config_file)
            )

        # Validate the config file
        if not validate_config(config):
            raise ValueError(
                "Invalid config file: {}.  Please run: calm init dsl".format(
                    user_config_file
                )
            )

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

    config_file = get_user_config_file()
    LOG.debug("Fetching configuration from '{}'".format(config_file))
    print("")
    with open(config_file) as fd:
        print(fd.read())
