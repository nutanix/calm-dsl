import click
import sys

from calm.dsl.cli.projects import create_project_from_dsl

from .network_group import (
    create_network_group_tunnel_from_dsl,
    create_network_group_tunnel_vm_from_dsl,
    delete_network_group_tunnel,
    describe_network_group,
    describe_network_group_tunnel,
    get_network_group_tunnels,
    get_network_groups,
)

from .main import create, get, delete, describe, reset
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@get.command("network-groups", feature_min_version="3.5.0")
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only project names"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_network_groups(limit, offset, quiet, out):
    """Get Network Groups, optionally filtered by a string"""

    get_network_groups(limit, offset, quiet, out)


@get.command("network-group-tunnels", feature_min_version="3.5.0")
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only project names"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_network_group_tunnels(limit, offset, quiet, out):
    """Get Network Group Tunnels, optionally filtered by a string"""

    get_network_group_tunnels(limit, offset, quiet, out)


@describe.command("network-group", feature_min_version="3.5.0")
@click.argument("network_group_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_network_group(network_group_name, out):
    """Describe a Network Group"""

    describe_network_group(network_group_name, out)


@describe.command("network-group-tunnel", feature_min_version="3.5.0")
@click.argument("network_group_tunnel_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_network_group(network_group_tunnel_name, out):
    """Describe a Network Group Tunnel"""

    describe_network_group_tunnel(network_group_tunnel_name, out)


@create.command("network-group-tunnel", feature_min_version="3.5.0")
@click.option(
    "--file",
    "-f",
    "network_group_tunnel_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Network Group Tunnel spec file to upload",
    required=True,
)
@click.option(
    "--name",
    "-n",
    "name",
    type=str,
    default="",
    help="Network Group Tunnel name(optional)",
)
@click.option(
    "--description", "-d", default=None, help="Network Group description (Optional)"
)
def _create_network_group_tunnel(name, network_group_tunnel_file, description):
    """Creates a Network Group and its Tunnel"""

    if network_group_tunnel_file.endswith(".py"):
        create_network_group_tunnel_from_dsl(
            network_group_tunnel_file, name, description
        )
    else:
        LOG.error("Unknown file format")
        return


@delete.command("network-group-tunnel")
@click.argument("network_group_tunnel_names", nargs=-1)
def _delete_network_group_tunnel(network_group_tunnel_names):
    """Deletes a Network Group and its Tunnel"""

    delete_network_group_tunnel(network_group_tunnel_names)


@reset.command(
    "network-group-tunnel-vm", feature_min_version="3.7.0", experimental=True
)
@click.option(
    "--file",
    "-f",
    "network_group_tunnel_vm_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of Network Group Tunnel VM spec file to upload",
    required=True,
)
@click.option(
    "--tunnel_name",
    "-n",
    "network_group_tunnel_name",
    type=str,
    required=True,
    help="Network Group Tunnel name",
)
def _reset_network_group_tunnel_vm(
    network_group_tunnel_vm_file, network_group_tunnel_name
):
    """Deploy a new Tunnel VM for a Network Group Tunnel"""

    if network_group_tunnel_vm_file.endswith(".py"):
        create_network_group_tunnel_vm_from_dsl(
            network_group_tunnel_vm_file, network_group_tunnel_name
        )
    else:
        LOG.error("Unknown file format")
        return
