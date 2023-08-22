import click

from calm.dsl.log import get_logging_handle

from .main import describe
from .providers import describe_custom_provider

LOG = get_logging_handle(__name__)


@describe.command("provider")
@click.argument("provider_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_provider(provider_name, out):
    """Describe a provider"""

    describe_custom_provider(provider_name, out)
