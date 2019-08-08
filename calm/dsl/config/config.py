import os
import configparser


# Defaults to be used if no config file exists.
# TODO - remove username/password
PC_IP = "10.45.5.30" #"10.46.34.230"
PC_PORT = 9440
PC_USERNAME = "admin"
PC_PASSWORD = "NTNX4ever/" #"***REMOVED***"

CONFIG_FILE = os.path.expanduser("~/server/config.ini")


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
