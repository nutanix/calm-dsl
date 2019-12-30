import os
import errno
import configparser
from jinja2 import Environment, PackageLoader


_CONFIG = None


def render_config_template(
    ip,
    port,
    username,
    password,
    project_name,
    db_location,
    schema_file="config.ini.jinja2",
):

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)
    text = template.render(
        ip=ip,
        port=port,
        username=username,
        password=password,
        project_name=project_name,
        db_location=db_location,
    )
    return text.strip() + "\n"


def get_config_file():

    # Default user config file
    # TODO - Check if config.ini is present in cwd
    user_config_file = os.path.join(os.path.expanduser("~/.calm/"), "config.ini")

    return user_config_file


def init_config(ip, port, username, password, project_name, db_location):

    user_config_file = get_config_file()

    # Create parent directory if not present
    if not os.path.exists(os.path.dirname(user_config_file)):
        try:
            os.makedirs(os.path.dirname(user_config_file))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    # Render config template
    text = render_config_template(
        ip, port, username, password, project_name, db_location
    )

    # Write config
    with open(user_config_file, "w") as fd:
        fd.write(text)


def get_config():
    global _CONFIG
    if not _CONFIG:
        # Create config object
        user_config_file = get_config_file()
        config = configparser.ConfigParser()
        config.optionxform = str  # Maintaining case sensitivity for field names
        config.read(user_config_file)
        _CONFIG = config
    return _CONFIG
