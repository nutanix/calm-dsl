import click

from .main import config, get
from .configs import set_config, print_config


@config.command("server")
@click.option("--ip", default=None, help="Prism Central server IP or hostname")
@click.option(
    "--port", default=None, help="Prism Central server port number"
)
@click.option("--username", envvar="PRISM_USERNAME", help="Prism Central username")
@click.option("--password", default=None, help="Prism Central password")
def set_server_config(ip, port, username, password):
    """Sets the configuration for Server"""
    set_config("SERVER", ip=ip, port=port, username=username, password=password)


@config.command("project")
@click.option("--name", default=None, help="Project Name")
@click.option("--uuid", default=None, help="Project UUID")
def set_project_config(name, uuid):
    """Sets the configuration for default project"""
    set_config("PROJECT", name=name, uuid=uuid)


@config.command("db")
@click.option("--location", default=None, help="Project Name")
def set_db_config(location):
    """Sets the configuration for local database"""
    set_config("DATABASE", location=location)


@get.command("config")
def _get_config():
    """Prints the server, project and categories etc/ configuration"""
    print_config()
