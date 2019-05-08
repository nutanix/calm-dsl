import os
import configparser

from calm.dsl.utils.server_utils import get_api_client as _get_api_client


# Defaults to be used if no config file exists.
# TODO - remove username/password
PC_IP = "10.46.34.230"
PC_PORT = 9440
PC_USERNAME = "admin"
PC_PASSWORD = "***REMOVED***"
CONFIG_FILE = "~/.calm/config"


_CONFIG = None


def get_config(ip=None, port=None, username=None, password=None, config_file=None):
    global _CONFIG
    if not _CONFIG:
        _CONFIG = _init_config(ip, port, username, password, config_file)
    return _CONFIG


def _init_config(ip, port, username, password, config_file):

    ip = ip or PC_IP
    port = port or PC_PORT
    username = username or PC_USERNAME
    password = password or PC_PASSWORD
    config_file = config_file or CONFIG_FILE

    config = configparser.ConfigParser()

    if os.path.isfile(config_file):
        config.read(config_file)

    if "SERVER" not in config:
        config["SERVER"] = {
            "pc_ip": ip,
            "pc_port": port,
            "pc_username": username,
            "pc_password": password,
        }
    else:
        config["SERVER"].setdefault("pc_ip", ip)
        config["SERVER"].setdefault("pc_port", port)
        config["SERVER"].setdefault("pc_username", username)
        config["SERVER"].setdefault("pc_password", password)

    return config


def get_api_client():

    config = get_config()

    pc_ip = config["SERVER"].get("pc_ip")
    pc_port = config["SERVER"].get("pc_port")
    username = config["SERVER"].get("pc_username")
    password = config["SERVER"].get("pc_password")

    return _get_api_client(pc_ip=pc_ip, pc_port=pc_port, auth=(username, password))
