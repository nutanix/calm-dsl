from calm.dsl.config import get_context
from .main import show


@show.command("config")
def show_config():
    """Shows server configuration"""

    ContextObj = get_context()
    ContextObj.print_config()
