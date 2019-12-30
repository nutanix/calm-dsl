from .main import show
from .configs import print_config


@show.command("config")
def show_config():
    print_config()
