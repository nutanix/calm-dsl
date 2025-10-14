import json
import click
import arrow
import time
import sys
import uuid
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins.models.helper.common import policy_required
from calm.dsl.store import Cache

from calm.dsl.constants import TUNNEL, CACHE
from .utils import (
    get_name_query,
    highlight_text,
    get_states_filter,
)

LOG = get_logging_handle(__name__)


def handle_err(err_msg):
    """Handles error by logging error message and exiting"""
    LOG.error(err_msg)
    sys.exit(err_msg)


def prepare_backend_filter_query(filter):
    """
    Resolves a comma-separated UI-facing filter string into a backend-compatible query format.

    This function is primarily used to:
      - Normalize whitespace in the input.
      - Validate filter format (expecting key==value pairs).
      - Map UI states to backend-defined state constants
    Example usage for filter_by:
    1. Converting UI states to backend states:
        Input:
            --filter "state==ACTIVE, state==ERROR, state==DELETED, state==VALIDATING"
        Output:
            "state==HEALTHY, state==UNHEALTHY, state==DELETED, state==ACTIVE"
    2. Handling extra spaces:
        Input:
            --filter "state==ACTIVE,    state==DELETED,   "
        Output:
            "state==HEALTHY, state==DELETED"
    3. Skipping empty conditions:
        Input:
            --filter "state==ACTIVE, , state==DELETED"
        Output:
            "state==HEALTHY, state==DELETED"
    4. Invalid format (raises error):
        Input:
            --filter "state=ACTIVE"
        Error:
            Invalid filter format. Expected 'state==value' format.
    """
    resolved_filters = []
    for condition in filter.split(","):
        condition = condition.strip()
        if not condition:
            continue
        if "==" not in condition:
            handle_err("Invalid filter format. Expected 'state==value' fomat.")
        parts = condition.split("==", 1)
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            handle_err("Invalid filter: missing key or value.")
        key, value = map(str.strip, parts)
        backend_state = (
            TUNNEL.UI_TO_BACKEND_STATE_MAPPING.get(value, "")
            if key == "state"
            else value
        )
        if key == "state" and not backend_state:
            handle_err("Please enter a valid state for tunnel.")
        resolved_filters.append("{}=={}".format(key, backend_state))
    return ", ".join(resolved_filters) if resolved_filters else ""


@policy_required
def get_tunnels_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get Tunnels, optionally filtered by a string."""
    client = get_api_client()
    params = {"length": limit, "offset": offset, "filter": "type!=network_group"}

    if name:
        params["filter"] += ";" + get_name_query([name])
    if filter_by:
        filter_by = prepare_backend_filter_query(filter_by)
        params["filter"] += ";" + "({})".format(filter_by)
    if all_items:
        params["filter"] += get_states_filter(TUNNEL.STATES)

    LOG.debug("Fetching tunnels with params: {}".format(params))
    res, err = client.tunnel.list(params=params)
    if err:
        ContextObj = get_context()
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]
        LOG.warning("Cannot fetch tunnels from {}".format(pc_ip))
        return

    res = res.json()
    total_matches = res["metadata"]["total_matches"]
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    if out == "json":
        click.echo(json.dumps(res, indent=4, separators=(",", ": ")))
        return

    json_rows = res["entities"]
    if not json_rows:
        click.echo(highlight_text("No tunnels found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "DESCRIPTION",
        "CREATED_BY",
        "STATE",
        "ASSOCIATED ACCOUNTS",
        "CREATED AT",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]
        resources = row.get("resources", {})

        name = row.get("name", "-")
        description = row.get("description", "-")
        created_by = metadata.get("owner_reference", "-").get("name", "-")
        backend_state = row.get("state", "-")
        state = TUNNEL.BACKEND_TO_UI_STATE_MAPPING.get(backend_state, "")
        if not state:
            handle_err("Tunnel found with invalid state: {}".format(state))

        associated_accounts = ""
        for account in resources.get("associated_account_refs", []):
            associated_accounts += account.get("name", "-") + ", "
        associated_accounts = associated_accounts[:-2] if associated_accounts else "-"

        creation_time = int(metadata.get("creation_time")) // 1000000
        creation_time = (
            "{}".format(arrow.get(creation_time).humanize()) if creation_time else "-"
        )

        uuid = metadata.get("uuid", "-")

        table.add_row(
            [
                highlight_text(name),
                highlight_text(description),
                highlight_text(created_by),
                highlight_text(state),
                highlight_text(associated_accounts),
                highlight_text(creation_time),
                highlight_text(uuid),
            ]
        )

    click.echo(table)


@policy_required
def get_tunnel(client, tunnel_name):
    """Fetches a tunnel by name"""

    params = {"filter": "name=={}".format(tunnel_name)}
    res, err = client.tunnel.list(params=params)
    if err:
        handle_err("Error fetching tunnel {}: {}".format(tunnel_name, err))

    res = res.json()
    entities = res.get("entities", [])
    tunnel = None
    if entities:
        if len(entities) > 1:
            handle_err(
                "Multiple tunnels found with name: {}. Please use UUID to specify the tunnel.".format(
                    tunnel_name
                )
            )

        LOG.info("Tunnel with name {} found.".format(tunnel_name))
        tunnel = entities[0]
    else:
        handle_err("Tunnel with name {} not found.".format(tunnel_name))
    return tunnel


def check_tunnel_usage(client, tunnel_name, tunnel_uuid):
    """
    Calls tunnel entity_references and returns (in_use: bool, err_out: dict or None)
    """
    res, err = client.tunnel.entity_references(tunnel_uuid, ignore_error=True)
    if err is not None:
        LOG.warning(
            "Could not fetch tunnel {} entity references. Proceeding with delete.".format(
                tunnel_name
            )
        )
        return False, err

    try:
        refs = res.json() or {}
    except Exception:
        refs = {}

    LOG.info(
        "Tunnel with name {} entity references found:\n{}".format(
            tunnel_name, json.dumps(refs, indent=4, separators=(",", ": "))
        )
    )
    in_use = {k: v for k, v in refs.items() if isinstance(v, list) and v}
    if in_use:
        message_list = [
            {
                "message": "Tunnel is associated with '{}' {}".format(str(len(lst)), k),
                "reason": "ACTION_NOT_SUPPORTED",
            }
            for k, lst in in_use.items()
        ]
        err_body = {
            "api_version": "3.1",
            "code": 405,
            "kind": "tunnel",
            "message_list": message_list,
            "state": "ERROR",
        }
        err_out = {"error": err_body, "code": 405}
        LOG.info(
            "Tunnel {} can't be deleted:\n{}".format(
                tunnel_name, json.dumps(err_out, indent=4, separators=(",", ": "))
            )
        )
        return True, err_out

    return False, None


@policy_required
def delete_tunnel(tunnel_names, no_cache_update=False):
    """Deletes all the tunnels with the given names"""
    client = get_api_client()
    deleted_tunnel_uuids = []

    for tunnel_name in tunnel_names:
        tunnel = get_tunnel(client, tunnel_name)
        tunnel_uuid = tunnel["metadata"]["uuid"]
        in_use, err = check_tunnel_usage(client, tunnel_name, tunnel_uuid)
        if in_use:
            LOG.info("Tunnel delete skipped for {}".format(tunnel_name))
            continue
        resp, err = client.tunnel.delete(uuid=tunnel_uuid)
        if err:
            LOG.exception(
                "Tunnel delete failed for {}: [{}] - {}".format(
                    tunnel_name, err["code"], err["error"]
                )
            )
            continue
        deleted_tunnel_uuids.append(tunnel_uuid)
        LOG.info("Tunnel {} deleted successfully.".format(tunnel_name))
    if deleted_tunnel_uuids:
        if no_cache_update:
            LOG.info("Skipping tunnels cach update.")
        else:
            LOG.info("Updating Tunnels cache ...")
            for _tunnel_id in deleted_tunnel_uuids:
                Cache.delete_one(entity_type=CACHE.ENTITY.TUNNEL, uuid=_tunnel_id)
            LOG.info("[Done]")


@policy_required
def describe_tunnel(tunnel_name, out):
    """Describe a Tunnel"""
    client = get_api_client()

    tunnel = get_tunnel(client, tunnel_name)

    if out == "json":
        click.echo(json.dumps(tunnel, indent=4, separators=(",", ": ")))
        return

    name = tunnel.get("metadata", {}).get("name")
    uuid = tunnel.get("metadata", {}).get("uuid")
    description = tunnel.get("status", {}).get("description", "")
    backend_state = tunnel.get("status", {}).get("state")
    state = (
        TUNNEL.BACKEND_TO_UI_STATE_MAPPING.get(backend_state, "")
        if backend_state
        else None
    )
    if not state:
        handle_err("Tunnel found with invalid state: {}".format(state))
    associated_accounts = ""
    for account in (
        tunnel.get("status", {}).get("resources", {}).get("associated_account_refs", [])
    ):
        associated_accounts += account.get("name", "-") + ", "
    associated_accounts = associated_accounts[:-2] if associated_accounts else "-"
    created_by = tunnel.get("metadata", {}).get("owner_reference", {}).get("name", "-")
    creation_time = int(tunnel.get("metadata", {}).get("creation_time", 0)) // 1000000
    past = arrow.get(creation_time).humanize() if creation_time else "-"
    created_on = time.ctime(creation_time)

    click.echo("\n----Tunnel Summary----\n")
    click.echo("Name: {} (uuid: {})".format(highlight_text(name), highlight_text(uuid)))
    click.echo("Description: " + highlight_text(description))
    click.echo("Status: " + highlight_text(state))
    click.echo("Associated Accounts: " + highlight_text(associated_accounts))
    click.echo("Created By: " + highlight_text(created_by))
    click.echo(
        "Created: {} ({})\n ".format(highlight_text(created_on), highlight_text(past))
    )


@policy_required
def create_tunnel_payload(name, description):
    if not name:
        handle_err("Tunnel name is required.")

    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_user = server_config["pc_username"]

    tunnel_payload = None
    spec = {
        "name": name,
        "description": description,
        "resources": {
            "created_by": pc_user,
        },
    }
    metadata = {"kind": "tunnel", "uuid": str(uuid.uuid4())}

    tunnel_payload = {
        "api_version": TUNNEL.API_VERSION,
        "metadata": metadata,
        "spec": spec,
    }
    return tunnel_payload


@policy_required
def create_tunnel(name="", description="", no_cache_update=False):
    """Creates a Tunnel"""
    client = get_api_client()
    LOG.info("Creating Tunnel with name: {}".format(name))
    tunnel_payload = create_tunnel_payload(name, description)

    res, err = client.tunnel.create(payload=tunnel_payload)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        return None, err

    tunnel = res.json()
    tunnel_uuid = tunnel["metadata"]["uuid"]
    tunnel_name = tunnel["metadata"]["name"]
    tunnel_status = tunnel.get("status", {})
    tunnel_state = tunnel_status.get("state", "DRAFT")
    LOG.debug("Tunnel {} has state {}".format(tunnel_name, tunnel_state))

    if tunnel_state != TUNNEL.UI_STATES.ACTIVE:
        msg_list = tunnel.get("status", {}).get("message_list", [])
        if not msg_list:
            LOG.debug(json.dumps(tunnel_status))
            handle_err(
                "Tunnel {} created with errors. Error: {}".format(
                    tunnel_name, err["error"]
                )
            )

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Tunnel {} created with {} error(s): {}".format(
                tunnel_name, len(msgs), ", ".join(msgs)
            )
        )

    LOG.info("Tunnel {} created successfully.".format(tunnel_name))

    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]

    link = "https://{}:{}/dm/self_service/settings/tunnels/{}".format(
        pc_ip, pc_port, tunnel_uuid
    )

    stdout_dict = {
        "name": tunnel_name,
        "link": link,
        "state": tunnel_state,
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    if no_cache_update:
        LOG.info("Skipping tunnels cache update.")
    else:
        LOG.info("Updating Tunnels cache ...")
        Cache.add_one(entity_type=CACHE.ENTITY.TUNNEL, uuid=tunnel_uuid)
        LOG.info("[Done]")


@policy_required
def update_tunnel(name, new_name="", description="", no_cache_update=False):
    """Updates a Tunnel"""
    client = get_api_client()
    LOG.info("Updating Tunnel with name: {}".format(name))

    tunnel_payload = get_tunnel(client, name)
    if not tunnel_payload:
        LOG.error("Tunnel {} not found.".format(name))
        return None, None

    tunnel_status = tunnel_payload.pop("status", None)
    tunnel_spec = {
        "name": new_name if new_name else tunnel_payload["metadata"]["name"],
        "description": description
        if description
        else tunnel_status.get("description", ""),
        "resources": {
            "created_by": tunnel_payload["metadata"]
            .get("owner_reference", {})
            .get("name", "")
        },
    }
    tunnel_payload["spec"] = tunnel_spec

    tunnel_uuid = tunnel_payload["metadata"]["uuid"]

    res, err = client.tunnel.update(uuid=tunnel_uuid, payload=tunnel_payload)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        return None, err

    tunnel = res.json()
    tunnel_name = tunnel["metadata"]["name"]
    tunnel_status = tunnel.get("status", {})
    tunnel_state = tunnel_status.get("state", "DRAFT")
    LOG.debug("Tunnel {} has state {}".format(tunnel_name, tunnel_state))

    if tunnel_state != TUNNEL.UI_STATES.ACTIVE:
        msg_list = tunnel.get("status", {}).get("message_list", [])
        if not msg_list:
            LOG.debug(json.dumps(tunnel_status))
            LOG.error("Tunnel {} updated with errors.".format(tunnel_name))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Tunnel {} updated with {} error(s): {}".format(
                tunnel_name, len(msgs), ", ".join(msgs)
            )
        )

    LOG.info("Tunnel {} updated successfully.".format(tunnel_name))

    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]

    link = "https://{}:{}/dm/self_service/settings/tunnels/{}".format(
        pc_ip, pc_port, tunnel_uuid
    )

    stdout_dict = {
        "name": tunnel_name,
        "link": link,
        "state": tunnel_state,
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    if no_cache_update:
        LOG.info("Skipping tunnels cache update.")
    else:
        LOG.info("Updating Tunnels cache ...")
        Cache.update_one(entity_type=CACHE.ENTITY.TUNNEL, uuid=tunnel_uuid)
        LOG.info("[Done]")
