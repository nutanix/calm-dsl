import click
import json
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.builtins import Ref
from .task_commands import watch_task
from .constants import ERGON_TASK
from calm.dsl.config import get_context
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle

from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_groups(name, filter_by, limit, offset, quiet, out):
    """Get the groups, optionally filtered by a string"""

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.group.list(params=params)

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch groups from {}".format(pc_ip))
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
        click.echo(highlight_text("No group found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            name = row["resources"]["directory_service_user_group"][
                "distinguished_name"
            ]

            # For user-groups having caps in the name
            try:
                name = _row["spec"]["resources"]["directory_service_user_group"][
                    "distinguished_name"
                ]
            except Exception:
                pass
            click.echo(highlight_text(name))
        return

    table = PrettyTable()
    table.field_names = ["NAME", "DISPLAY NAME", "TYPE", "STATE", "UUID"]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        # For user-groups having caps in the name
        name = row["resources"]["directory_service_user_group"]["distinguished_name"]
        try:
            name = _row["spec"]["resources"]["directory_service_user_group"][
                "distinguished_name"
            ]
        except Exception:
            pass

        table.add_row(
            [
                highlight_text(name),
                highlight_text(row["resources"].get("display_name", "")),
                highlight_text(row["resources"]["user_group_type"]),
                highlight_text(row["state"]),
                highlight_text(metadata["uuid"]),
            ]
        )

    click.echo(table)


def create_group(name):
    """creates user-group on pc"""

    client = get_api_client()
    group_payload = {
        "spec": {
            "resources": {"directory_service_user_group": {"distinguished_name": name}}
        },
        "metadata": {"kind": "user_group", "spec_version": 0},
    }

    res, err = client.group.create(group_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    stdout_dict = {
        "name": name,
        "uuid": res["metadata"]["uuid"],
        "execution_context": res["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    user_group_uuid = res["metadata"]["uuid"]
    LOG.info("Polling on user-group creation task")
    task_state = watch_task(
        res["status"]["execution_context"]["task_uuid"], poll_interval=5
    )
    if task_state in ERGON_TASK.FAILURE_STATES:
        LOG.exception("User-Group creation task went to {} state".format(task_state))
        sys.exit(-1)

    # Update user-groups in cache
    LOG.info("Updating user-groups cache ...")
    Cache.add_one(entity_type=CACHE.ENTITY.USER_GROUP, uuid=user_group_uuid)
    LOG.info("[Done]")


def delete_group(group_names):
    """deletes user-group on pc"""

    client = get_api_client()

    deleted_group_uuids = []
    for name in group_names:
        group_ref = Ref.Group(name)
        res, err = client.group.delete(group_ref["uuid"])
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        deleted_group_uuids.append(group_ref["uuid"])
        LOG.info("Polling on user-group deletion task")
        res = res.json()
        task_state = watch_task(
            res["status"]["execution_context"]["task_uuid"], poll_interval=5
        )
        if task_state in ERGON_TASK.FAILURE_STATES:
            LOG.exception(
                "User-Group deletion task went to {} state".format(task_state)
            )
            sys.exit(-1)

    # Update user-groups in cache
    if deleted_group_uuids:
        LOG.info("Updating user-groups cache ...")
        for _group_uuid in deleted_group_uuids:
            Cache.delete_one(entity_type=CACHE.ENTITY.USER_GROUP, uuid=_group_uuid)
        LOG.info("[Done]")
