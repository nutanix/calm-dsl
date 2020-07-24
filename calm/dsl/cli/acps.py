import time
import click
import arrow
import json
import sys
import uuid
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.config import get_config
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.builtins import Ref

from .constants import ACP
from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_acps(name, filter_by, limit, offset, quiet, out):
    """ Get the acps, optionally filtered by a string """

    client = get_api_client()
    config = get_config()

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

    res, err = client.acp.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
        LOG.warning("Cannot fetch acps from {}".format(pc_ip))
        return

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No acp found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "STATE",
        "UUID",
    ]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["state"]),
                highlight_text(metadata["uuid"]),
            ]
        )

    click.echo(table)


def get_system_roles():

    # 'Self-Service Admin', 'Prism Admin', 'Prism Viewer', 'Super Admin' are forbidden roles
    return ["Project Admin", "Operator", "Consumer", "Developer"]


def create_acp(role, project, user, group, name):

    client = get_api_client()
    acp_name = name or "nuCalmAcp-{}".format(str(uuid.uuid4()))

    # Check whether there is an existing acp with this name
    params = {"filter": "name=={}".format(acp_name)}
    res, err = client.acp.list(params=params)
    if err:
        return None, err

    response = res.json()
    entities = response.get("entities", None)

    if entities:
        LOG.error("ACP {} already exists.".format(acp_name))
        sys.exit(-1)

    project_cache_data = Cache.get_entity_data(entity_type="project", name=project)
    if not project_cache_data:
        LOG.error("Project {} not found. Please run: calm update cache".format(project))
        sys.exit(-1)

    project_uuid = project_cache_data["uuid"]
    whitelisted_subnets = project_cache_data["whitelisted_subnets"]

    cluster_uuids = []
    for subnet_uuid in whitelisted_subnets:
        subnet_cache_data = Cache.get_entity_data_using_uuid(
            entity_type="ahv_subnet", uuid=subnet_uuid
        )

        cluster_uuids.append(subnet_cache_data["cluster_uuid"])

    role_cache_data = Cache.get_entity_data(entity_type="role", name=role)
    role_uuid = role_cache_data["uuid"]

    # Check if there is an existing acp with given (project-role) tuple
    params = {
        "length": 1000,
        "filter": "role_uuid=={};project_reference=={}".format(role_uuid, project_uuid),
    }
    res, err = client.acp.list(params)
    if err:
        return None, err

    response = res.json()
    entities = response.get("entities", None)

    if entities:
        LOG.error(
            "ACP {} already exists for given role in project".format(
                entities[0]["status"]["name"]
            )
        )
        sys.exit(-1)

    # Creating filters for acp
    default_context = ACP.DEFAULT_CONTEXT

    # Setting project uuid in default context
    default_context["scope_filter_expression_list"][0]["right_hand_side"][
        "uuid_list"
    ] = [project_uuid]

    # Role specific filters
    entity_filter_expression_list = []
    if role == "Project Admin":
        entity_filter_expression_list = (
            ACP.ENTITY_FILTER_EXPRESSION_LIST.PROJECT_ADMIN
        )  # TODO remove index bases searching
        entity_filter_expression_list[4]["right_hand_side"]["uuid_list"] = [
            project_uuid
        ]

    elif role == "Developer":
        entity_filter_expression_list = ACP.ENTITY_FILTER_EXPRESSION_LIST.DEVELOPER

    elif role == "Consumer":
        entity_filter_expression_list = ACP.ENTITY_FILTER_EXPRESSION_LIST.CONSUMER

    elif role == "Operator" and cluster_uuids:
        entity_filter_expression_list = ACP.ENTITY_FILTER_EXPRESSION_LIST.CONSUMER

    if cluster_uuids:
        entity_filter_expression_list.append(
            {
                "operator": "IN",
                "left_hand_side": {"entity_type": "cluster",},
                "right_hand_side": {"uuid_list": cluster_uuids,},
            }
        )

    # TODO check these users are not present in project's other acps
    user_references = []
    for u in user:
        user_references.append(Ref.User(u))

    group_references = []
    for g in group:
        group_references.append(Ref.Group(g))

    context_list = [default_context]
    if entity_filter_expression_list:
        context_list.append(
            {"entity_filter_expression_list": entity_filter_expression_list}
        )

    acp_payload = {
        "spec": {
            "name": acp_name,
            "resources": {
                "role_reference": Ref.Role(role),
                "user_reference_list": user_references,
                "user_group_reference_list": group_references,
                "filter_list": {"context_list": context_list},
            },
        },
        "metadata": {
            "kind": "access_control_policy",
            "spec_version": 0,
            "project_reference": Ref.Project(project),
        },
    }

    res, err = client.acp.create(acp_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    print(json.dumps(res.json(), indent=4))
