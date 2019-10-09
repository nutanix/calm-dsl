import os
from calm.dsl.config import get_config


CONFIG_FILE = os.path.expanduser("~/calm-dsl-engine/config/server/config.ini")


def set_config(section, **kwargs):

    section_field_mapping = {
        "SERVER": {
            "ip": "pc_ip",
            "port": "pc_port",
            "username": "pc_username",
            "password": "pc_password",
        },
        "PROJECT": {"name": "name", "uuid": "uuid"},
    }

    config_parser = get_config()

    field_map = section_field_mapping[section]

    for key, value in kwargs.items():
        if value:
            config_parser.set(section, field_map[key], value)

    with open(CONFIG_FILE, "w") as configfile:
        config_parser.write(configfile)
