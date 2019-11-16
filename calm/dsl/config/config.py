import os
import configparser


# Default config file
CONFIG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.ini")


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
        _CONFIG = _init_config(ip, port, username, password, config_file, project_name)
    return _CONFIG


def get_config_file():
    return CONFIG_FILE


def _init_config(ip, port, username, password, config_file, project_name):

    global CONFIG_FILE
    config_file = config_file or CONFIG_FILE
    config = configparser.ConfigParser()
    config.optionxform = str  # Maintaining case sensitivity for field names

    if os.path.isfile(config_file):
        config.read(config_file)

    CONFIG_FILE = config_file
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
        stored_project_name = config["PROJECT"].get("name")
        if stored_project_name:
            if project_name and (project_name != stored_project_name):
                config.remove_option("PROJECT", "uuid")
        else:
            config.remove_option("PROJECT", "uuid")

        project_name = project_name or stored_project_name
        config["PROJECT"]["name"] = project_name

    else:
        config["PROJECT"] = {"name": project_name}

    if "CATEGORIES" not in config:
        config["CATEGORIES"] = {}

    return config
