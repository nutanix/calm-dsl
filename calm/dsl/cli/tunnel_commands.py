import click
from .main import get, create, update, describe, delete

from .tunnels import (
    get_tunnels_list,
    describe_tunnel,
    create_tunnel,
    update_tunnel,
    delete_tunnel,
)
from calm.dsl.constants import TUNNEL

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@get.command(
    "tunnels", feature_min_version=TUNNEL.FEATURE_MIN_VERSION, experimental=True
)
@click.option("--name", "-n", default=None, help="Search for tunnels by name")
@click.option(
    "--filter",
    "filter_by",
    "-f",
    default="",
    help=(
        "Filter tunnels by state. Valid states: VALIDATING, ACTIVE, ERROR, DELETED. "
        "Use the format 'state==STATE' to filter by a single state. "
        "To filter by multiple states, separate conditions with a comma, e.g., "
        "'state==ACTIVE, state==ERROR'."
    ),
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only tunnel names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_tunnels(name, filter_by, limit, offset, quiet, all_items, out):
    """Get Tunnels, optionally filtered by a string"""

    get_tunnels_list(name, filter_by, limit, offset, quiet, all_items, out)


@delete.command(
    "tunnels", feature_min_version=TUNNEL.FEATURE_MIN_VERSION, experimental=True
)
@click.argument("tunnel_names", nargs=-1)
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for tunnels",
)
def _delete_tunnels(tunnel_names, no_cache_update):
    """Deletes a Tunnel"""

    delete_tunnel(tunnel_names, no_cache_update=no_cache_update)


@describe.command("tunnel", feature_min_version=TUNNEL.FEATURE_MIN_VERSION)
@click.argument("tunnel_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [text|json].",
)
def _describe_tunnel(tunnel_name, out):
    """Describe a tunnel"""

    describe_tunnel(tunnel_name, out)


@create.command("tunnel", feature_min_version=TUNNEL.FEATURE_MIN_VERSION)
@click.option(
    "--name",
    "-n",
    "name",
    type=str,
    default="",
    required=True,
    help="Tunnel name (Required)",
)
@click.option(
    "--description",
    "-d",
    "description",
    type=str,
    default="",
    help="Tunnel description (Optional)",
)
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for tunnels",
)
def _create_tunnel(name, description, no_cache_update):
    """Creates Tunnel"""

    create_tunnel(name, description, no_cache_update=no_cache_update)


@update.command("tunnel", feature_min_version=TUNNEL.FEATURE_MIN_VERSION)
@click.argument("name", required=True, nargs=1)
@click.option(
    "--new-name",
    "-nn",
    "new_name",
    type=str,
    default="",
    help="Tunnel name (Optional), if not provided, original name will be used",
)
@click.option(
    "--description",
    "-d",
    "description",
    type=str,
    default=None,
    help="Tunnel description (Optional), if not provided, original description will be used",
)
@click.option(
    "--no-cache-update",
    "no_cache_update",
    is_flag=True,
    default=False,
    help="if true, cache is not updated for tunnels",
)
def _update_tunnel(name, new_name, description, no_cache_update):
    """Updates Tunnel"""

    update_tunnel(name, new_name, description, no_cache_update=no_cache_update)
