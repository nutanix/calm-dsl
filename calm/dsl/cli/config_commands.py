from calm.dsl.config import print_config
from .main import show


@show.command("config")
def show_config():
    """Shows server configuration"""

    print_config()
