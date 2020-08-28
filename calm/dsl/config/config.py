import os
import errno
import configparser

from jinja2 import Environment, PackageLoader
from .schema import validate_config, validate_init_config
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
_CONFIG_FILE = None


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


def get_init_data():
    """Returns the init configuration data"""

    init_file = get_init_file()
    if not os.path.exists(init_file):
        raise FileNotFoundError(
            "'{}' not found. Please run: calm init dsl".format(init_file)
        )

    init_config = configparser.ConfigParser()
    init_config.optionxform = str
    init_config.read(init_file)

    # Validate init config
    if not validate_init_config(init_config):
        raise ValueError(
            "Invalid init config file: {}. Please run: calm init dsl".format(init_file)
        )

    return init_config


def get_default_config_file():
    """Returns default location of config file"""

    user_config_file = os.path.join(os.path.expanduser("~"), ".calm", "config.ini")
    make_file_dir(user_config_file)
    return user_config_file


def get_user_config_file():
    """Returns the config file location"""

    global _CONFIG_FILE
    cwd = os.getcwd()

    if "config.ini" in os.listdir(cwd):
        config_file = os.path.join(cwd, "config.ini")
        return config_file

    if not _CONFIG_FILE:
        try:
            init_obj = get_init_data()
            _CONFIG_FILE = init_obj["CONFIG"]["location"] or get_default_config_file()

        except FileNotFoundError:
            _CONFIG_FILE = get_default_config_file()

    return _CONFIG_FILE


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


def update_config_file_location(config_file):
    """
    updates the config file location (global _CONFIG_FILE object)
    If update_init is True, it will update the config file location at init file also
    """

    global _CONFIG_FILE

    # Check presence of file
    if not os.path.exists(config_file):
        raise FileNotFoundError("Config file '{}' not found.".format(config_file))

    config = configparser.ConfigParser()
    config.optionxform = str  # Maintaining case sensitivity for field names
    config.read(config_file)

    # Validate the config file
    if not validate_config(config):
        raise ValueError("Invalid config file: {}.".format(config_file))

    # If file exists and a valid config file then update global _CONFIG_FILE object
    _CONFIG_FILE = config_file


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


def update_init_config(config_file, db_file, local_dir):
    """updates the init file data"""

    # create required directories
    make_file_dir(config_file)
    make_file_dir(db_file)
    make_file_dir(local_dir, is_dir=True)

    # Note: No need to validate init data as it is rendered by template
    init_file = get_init_file()
    LOG.debug("Rendering init template")
    text = _render_init_template(config_file, db_file, local_dir)

    # Write init configuration
    LOG.debug("Writing configuration to '{}'".format(init_file))
    with open(init_file, "w") as fd:
        fd.write(text)


def update_config(host, port, username, password, project_name, log_level):
    """Updates the config file data"""

    config_file = get_user_config_file()

    LOG.debug("Rendering configuration template")
    text = _render_config_template(
        host, port, username, password, project_name, log_level
    )

    LOG.debug("Writing configuration to '{}'".format(config_file))
    with open(config_file, "w") as fd:
        fd.write(text)


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
    """
    overrides the existing server/dsl configuration
    Note: This helper assumes that valid configuration is present. It is invoked just to update the existing configuration.

    if config_file is given, it will update config file location in `init.ini` and update the server details in that file
    """

    init_obj = get_init_data()

    if config_file:
        # Validate config file and update _CONFIG_FILE object
        update_config_file_location(config_file)

    # TODO check pipelining of commands with changing db_location and local_dir should work
    db_location = db_location or init_obj["DB"]["location"]
    local_dir_location = local_dir or init_obj["LOCAL_DIR"]["location"]
    config_file_location = config_file or init_obj["CONFIG"]["location"]

    update_init_config(
        config_file=config_file_location,
        db_file=db_location,
        local_dir=local_dir_location,
    )

    config = get_config()
    host = host or config["SERVER"]["pc_ip"]
    username = username or config["SERVER"]["pc_username"]
    port = port or config["SERVER"]["pc_port"]
    password = password or config["SERVER"]["pc_password"]
    project_name = project_name or config["PROJECT"]["name"]
    log_level = log_level or config["LOG"]["level"]

    logging_levels = LOG.get_logging_levels()
    if log_level not in logging_levels:
        raise ValueError("Invalid log level. Select from {}".format(logging_levels))

    update_config(
        host=host,
        port=port,
        username=username,
        password=password,
        project_name=project_name,
        log_level=log_level,
    )


def get_config():

    global _CONFIG_FILE

    if not _CONFIG_FILE:
        # Get config file from init file
        init_obj = get_init_data()
        config_file = init_obj["CONFIG"]["location"]

    else:
        config_file = _CONFIG_FILE

    # Parse the config file
    config = configparser.ConfigParser()
    config.optionxform = str  # Maintaining case sensitivity for field names
    config.read(config_file)

    # Validate the config file
    if not validate_config(config):
        raise ValueError(
            "Invalid config file: {}. Please run calm init dsl".format(config_file)
        )

    return config


def print_config():
    """prints the configuration"""

    config_file = get_user_config_file()
    LOG.debug("Fetching configuration from '{}'".format(config_file))
    print("")
    with open(config_file) as fd:
        print(fd.read())
