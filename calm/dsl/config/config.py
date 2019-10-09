import os
import configparser


# Defaults to be used if no config file exists.
# TODO - remove username/password
PC_IP = "10.46.34.230"
PC_PORT = "9440"
PC_USERNAME = "admin"
PC_PASSWORD = "***REMOVED***"
PROJECT_NAME = "default"
CONFIG_FILE = os.path.expanduser("~/calm-dsl-engine/config/server/config.ini")


_CONFIG = None


def get_config(ip=None, port=None, username=None, password=None, config_file=None, project_name=None):
    global _CONFIG
    if not _CONFIG:
        _CONFIG = _init_config(ip, port, username, password, config_file, project_name)
    return _CONFIG


def _init_config(ip, port, username, password, config_file, project_name):

    config_file = config_file or CONFIG_FILE
    config = configparser.ConfigParser()

    if os.path.isfile(config_file):
        config.read(config_file)

    if "SERVER" in config:
        ip = ip or config["SERVER"].get("pc_ip")
        port = port or config["SERVER"].get("pc_port")
        username = username or config["SERVER"].get("pc_username")
        password = password or config["SERVER"].get("pc_password")

    ip = ip or PC_IP
    port = port or PC_PORT
    username = username or PC_USERNAME
    password = password or PC_PASSWORD

    config["SERVER"] = {
        "pc_ip": ip,
        "pc_port": port,
        "pc_username": username,
        "pc_password": password,
    }

    if "PROJECT" in config:
        stored_project_name = config["PROJECT"].get("name")
        if stored_project_name:
            if project_name != stored_project_name:
                config.remove_option("PROJECT", "uuid")
        else:
            config.remove_option("PROJECT", "uuid")

        project_name = project_name or stored_project_name
        project_name = project_name or PROJECT_NAME
        config["PROJECT"]["name"] = project_name

    else:
        config["PROJECT"] = {
            "name": project_name or PROJECT_NAME
        }

    return config
