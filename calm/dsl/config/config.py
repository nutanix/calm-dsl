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
        config["SERVER"]["pc_ip"] = ip or config["SERVER"]["pc_ip"]
        config["SERVER"]["pc_port"] = port or config["SERVER"]["pc_port"]
        config["SERVER"]["pc_username"] = username or config["SERVER"]["pc_username"]
        config["SERVER"]["pc_password"] = password or config["SERVER"]["pc_password"]

    if "PROJECT" in config:
        config["PROJECT"]["name"] = project_name or config["PROJECT"]["name"]

    config["SERVER"].setdefault("pc_ip", PC_IP)
    config["SERVER"].setdefault("pc_port", PC_PORT)
    config["SERVER"].setdefault("pc_username", PC_USERNAME)
    config["SERVER"].setdefault("pc_password", PC_PASSWORD)
    config["PROJECT"].setdefault("name", PROJECT_NAME)

    return config
