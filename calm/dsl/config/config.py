import os
import configparser


# config file template
CONFIG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.ini")

# User config file
USER_CONFIG_DIRECTORY = os.path.expanduser("~/.calm/")
USER_CONFIG_FILE = os.path.expanduser("~/.calm/config.ini")


_CONFIG = None


def get_config(
    ip=None,
    port=None,
    username=None,
    password=None,
    config_file=None,
    project_name=None,
):
    global _CONFIG
    if not _CONFIG:
        update_config(ip, port, username, password, config_file, project_name)
    return _CONFIG


def update_config(
    ip=None,
    port=None,
    username=None,
    password=None,
    config_file=None,
    project_name=None,
    db_location=None,
):
    global _CONFIG
    _CONFIG = _init_config(
        ip, port, username, password, config_file, project_name, db_location
    )


def get_config_file():
    return USER_CONFIG_FILE


def _init_config(ip, port, username, password, config_file, project_name, db_location):

    global CONFIG_FILE
    global USER_CONFIG_FILE

    config = configparser.ConfigParser()
    config.optionxform = str  # Maintaining case sensitivity for field names

    # If user file not exists, it will create one
    if not os.path.exists(USER_CONFIG_FILE):
        # Creating directory
        if not os.path.isdir(USER_CONFIG_DIRECTORY):
            os.makedirs(os.path.dirname(USER_CONFIG_FILE))

        # Writing the template for config in user's place
        config.read(CONFIG_FILE)
        with open(USER_CONFIG_FILE, "w+") as user_config_file:
            config.write(user_config_file)

    config_file = config_file or USER_CONFIG_FILE
    config = configparser.ConfigParser()
    config.optionxform = str  # Maintaining case sensitivity for field names

    if os.path.isfile(config_file):
        config.read(config_file)

    USER_CONFIG_FILE = config_file
    if "SERVER" in config:
        ip = ip or config["SERVER"].get("pc_ip")
        port = port or config["SERVER"].get("pc_port")
        username = username or config["SERVER"].get("pc_username")
        password = password or config["SERVER"].get("pc_password")

    config["SERVER"] = {
        "pc_ip": ip,
        "pc_port": port,
        "pc_username": username,
        "pc_password": password,
    }

    if "PROJECT" in config:
        project_name = project_name or config["PROJECT"].get("name")

    config["PROJECT"] = {"name": project_name}

    if "DB" in config:
        db_location = db_location or config["DB"].get("location")
    else:
        config["DB"] = {
            "location": db_location or os.path.expanduser("~/.calm/dsl.db"),
        }

    if "CATEGORIES" not in config:
        config["CATEGORIES"] = {}

    return config


def get_db_location():

    config = get_config()

    db_location = None
    if "DB" in config:
        db_location = config["DB"].get("location", None)

    if not db_location:
        # Default DB location
        db_location = os.path.expanduser("~/.calm/dsl.db")

    return db_location
