import click
import json
import sys
import uuid
from prettytable import PrettyTable

from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.builtins import Ref

from .constants import ACP
from .task_commands import watch_task
from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_acps(name, project_name, filter_by, limit, offset, quiet, out):
    """ Get the acps, optionally filtered by a string """

    client = get_api_client()

    params = {"length": 1000}
    project_name_uuid_map = client.project.get_name_uuid_map(params)

    project_uuid = project_name_uuid_map.get(project_name, "")
    if not project_uuid:
        LOG.error("Project '{}' not found".format(project_name))
        sys.exit(-1)

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if project_uuid:
        filter_query = filter_query + ";(project_reference=={})".format(project_uuid)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.acp.list(params=params)

    if err:
        ContextObj = get_context()
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]

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
        "REFERENCED_ROLE",
        "REFERENCED_PROJECT",
        "UUID",
    ]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        role_ref = row["resources"].get("role_reference", {})
        role = role_ref.get("name", "-")

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["state"]),
                highlight_text(role),
                highlight_text(project_name),
                highlight_text(metadata["uuid"]),
            ]
        )

    click.echo(table)


def get_system_roles():

    # 'Self-Service Admin', 'Prism Admin', 'Prism Viewer', 'Super Admin' are forbidden roles
    return ["Project Admin", "Operator", "Consumer", "Developer"]


def create_acp(role, project, acp_users, acp_groups, name):

    if not (acp_users or acp_groups):
        LOG.error("Atleast single user/group should be given")
        sys.exit(-1)

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

    params = {"length": 1000}
    project_name_uuid_map = client.project.get_name_uuid_map(params)

    project_uuid = project_name_uuid_map.get(project, "")
    if not project_uuid:
        LOG.error("Project '{}' not found".format(project))
        sys.exit(-1)

    LOG.info("Fetching project '{}' details".format(project))
    ProjectInternalObj = get_resource_api("projects_internal", client.connection)
    res, err = ProjectInternalObj.read(project_uuid)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project_payload = res.json()
    project_payload.pop("status", None)
    project_resources = project_payload["spec"]["project_detail"].get("resources", "")

    # Check if users are present in project
    project_users = []
    for user in project_resources.get("user_reference_list", []):
        project_users.append(user["name"])

    if not set(acp_users).issubset(set(project_users)):
        LOG.error(
            "Users {} are not registered in project".format(
                set(acp_users).difference(set(project_users))
            )
        )
        sys.exit(-1)

    # Check if groups are present in project
    project_groups = []
    for group in project_resources.get("external_user_group_reference_list", []):
        project_groups.append(group["name"])

    if not set(acp_groups).issubset(set(project_groups)):
        LOG.error(
            "Groups {} are not registered in project".format(
                set(acp_groups).difference(set(project_groups))
            )
        )
        sys.exit(-1)

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

    # Constructing ACP payload --------

    # Getting the cluster uuids for acp
    whitelisted_subnets = []
    for subnet in project_resources.get("subnet_reference_list", []):
        whitelisted_subnets.append(subnet["uuid"])

    for subnet in project_resources.get("external_network_list", []):
        whitelisted_subnets.append(subnet["uuid"])

    cluster_uuids = []
    for subnet_uuid in whitelisted_subnets:
        subnet_cache_data = Cache.get_entity_data_using_uuid(
            entity_type="ahv_subnet", uuid=subnet_uuid
        )

        cluster_uuids.append(subnet_cache_data["cluster_uuid"])

    # Default context for acp
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
                "left_hand_side": {"entity_type": "cluster"},
                "right_hand_side": {"uuid_list": cluster_uuids},
            }
        )

    # TODO check these users are not present in project's other acps
    user_references = []
    user_name_uuid_map = client.user.get_name_uuid_map({"length": 1000})
    for u in acp_users:
        user_references.append(
            {"kind": "user", "name": u, "uuid": user_name_uuid_map[u]}
        )

    usergroup_name_uuid_map = client.group.get_name_uuid_map({"length": 1000})
    group_references = []
    for g in acp_groups:
        group_references.append(
            {"kind": "user_group", "name": g, "uuid": usergroup_name_uuid_map[g]}
        )

    context_list = [default_context]
    if entity_filter_expression_list:
        context_list.append(
            {"entity_filter_expression_list": entity_filter_expression_list}
        )

    acp_payload = {
        "acp": {
            "name": acp_name,
            "resources": {
                "role_reference": Ref.Role(role),
                "user_reference_list": user_references,
                "user_group_reference_list": group_references,
                "filter_list": {"context_list": context_list},
            },
        },
        "metadata": {"kind": "access_control_policy"},
        "operation": "ADD",
    }

    # Appending acp payload to project
    acp_list = project_payload["spec"].get("access_control_policy_list", [])
    for _acp in acp_list:
        _acp["operation"] = "UPDATE"

    acp_list.append(acp_payload)
    project_payload["spec"]["access_control_policy_list"] = acp_list

    LOG.info("Creating acp {}".format(acp_name))
    res, err = ProjectInternalObj.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    stdout_dict = {
        "name": acp_name,
        "execution_context": res["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))
    LOG.info("Polling on acp creation task")
    watch_task(res["status"]["execution_context"]["task_uuid"])


def delete_acp(acp_name, project_name):

    client = get_api_client()

    params = {"length": 1000}
    project_name_uuid_map = client.project.get_name_uuid_map(params)

    project_uuid = project_name_uuid_map.get(project_name, "")
    if not project_uuid:
        LOG.error("Project '{}' not found.".format(project_name))
        sys.exit(-1)

    LOG.info("Fetching project '{}' details".format(project_name))
    ProjectInternalObj = get_resource_api("projects_internal", client.connection)
    res, err = ProjectInternalObj.read(project_uuid)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project_payload = res.json()
    project_payload.pop("status", None)

    is_acp_present = False
    for _row in project_payload["spec"].get("access_control_policy_list", []):
        if _row["acp"]["name"] == acp_name:
            _row["operation"] = "DELETE"
            is_acp_present = True
        else:
            _row["operation"] = "UPDATE"

    if not is_acp_present:
        LOG.error(
            "ACP({}) is not associated with project({})".format(acp_name, project_name)
        )
        sys.exit(-1)

    LOG.info(
        "Deleting acp '{}' associated with project '{}'".format(acp_name, project_name)
    )
    res, err = ProjectInternalObj.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    stdout_dict = {
        "name": acp_name,
        "execution_context": res["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))
    LOG.info("Polling on acp deletion task")
    watch_task(res["status"]["execution_context"]["task_uuid"])


def describe_acp(acp_name, project_name, out):

    client = get_api_client()

    params = {"length": 1000}
    project_name_uuid_map = client.project.get_name_uuid_map(params)

    project_uuid = project_name_uuid_map.get(project_name, "")
    if not project_uuid:
        LOG.error("Project '{}' not found".format(project_name))
        sys.exit(-1)

    params = {
        "length": 1000,
        "filter": "(name=={});(project_reference=={})".format(acp_name, project_uuid),
    }
    acp_map = client.acp.get_name_uuid_map(params)

    acp_uuid = acp_map.get(acp_name, "")
    if not acp_uuid:
        LOG.error(
            "No ACP found with name '{}' and project '{}'".format(
                acp_name, project_name
            )
        )
        sys.exit(-1)

    LOG.info("Fetching acp {} details".format(acp_name))
    res, err = client.acp.read(acp_uuid)
    if err:
        LOG.error(err)
        sys.exit(-1)

    acp = res.json()
    if out == "json":
        click.echo(json.dumps(acp, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----ACP Summary----\n")
    click.echo("Name: " + highlight_text(acp_name) + " (uuid: " + acp_uuid + ")")
    click.echo("Status: " + highlight_text(acp["status"]["state"]))
    click.echo("Project: " + highlight_text(project_name))

    acp_users = acp["status"]["resources"].get("user_reference_list", [])
    acp_groups = acp["status"]["resources"].get("user_group_reference_list", [])
    acp_role = acp["status"]["resources"].get("role_reference", [])

    if acp_role:
        role_data = Cache.get_entity_data_using_uuid(
            entity_type="role", uuid=acp_role["uuid"]
        )
        if not role_data:
            LOG.error(
                "Role ({}) details not present. Please update cache".format(
                    acp_role["uuid"]
                )
            )
            sys.exit(-1)
        click.echo("Role: " + highlight_text(role_data["name"]))

    if acp_users:
        user_uuid_name_map = client.user.get_uuid_name_map({"length": 1000})
        click.echo("Users [{}]:".format(highlight_text(len(acp_users))))
        for user in acp_users:
            click.echo("\t" + highlight_text(user_uuid_name_map[user["uuid"]]))

    if acp_groups:
        usergroup_uuid_name_map = client.group.get_uuid_name_map({"length": 1000})
        click.echo("Groups [{}]:".format(highlight_text(len(acp_groups))))
        for group in acp_groups:
            click.echo("\t" + highlight_text(usergroup_uuid_name_map[group["uuid"]]))


def update_acp(
    acp_name,
    project_name,
    add_user_list,
    add_group_list,
    remove_user_list,
    remove_group_list,
):

    if not (add_user_list or add_group_list or remove_user_list or remove_group_list):
        LOG.error("Atleast single user/group should be given for add/remove operations")
        sys.exit(-1)

    client = get_api_client()

    params = {"length": 1000}
    project_name_uuid_map = client.project.get_name_uuid_map(params)

    project_uuid = project_name_uuid_map.get(project_name, "")
    if not project_uuid:
        LOG.error("Project '{}' not found".format(project_name))
        sys.exit(-1)

    LOG.info("Fetching project '{}' details".format(project_name))
    ProjectInternalObj = get_resource_api("projects_internal", client.connection)
    res, err = ProjectInternalObj.read(project_uuid)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project_payload = res.json()
    project_payload.pop("status", None)

    project_resources = project_payload["spec"]["project_detail"]["resources"]
    project_users = []
    project_groups = []
    for user in project_resources.get("user_reference_list", []):
        project_users.append(user["name"])

    for group in project_resources.get("external_user_group_reference_list", []):
        project_groups.append(group["name"])

    # Checking if to be added users/groups are registered in project
    if not set(add_user_list).issubset(set(project_users)):
        LOG.error(
            "Users {} are not registered in project".format(
                set(add_user_list).difference(set(project_users))
            )
        )
        sys.exit(-1)

    if not set(add_group_list).issubset(set(project_groups)):
        LOG.error(
            "Groups {} are not registered in project".format(
                set(add_group_list).difference(set(project_groups))
            )
        )
        sys.exit(-1)

    # Raise error if same user/group is present in both add/remove list
    common_users = set(add_user_list).intersection(set(remove_user_list))
    if common_users:
        LOG.error("Users {} are both in add_user and remove_user".format(common_users))
        sys.exit(-1)

    common_groups = set(add_group_list).intersection(set(remove_group_list))
    if common_groups:
        LOG.error(
            "Groups {} are present both in add_groups and remove_groups".format(
                common_groups
            )
        )
        sys.exit(-1)

    # Flag to check whether given acp is present in project or not
    is_acp_present = False
    for _row in project_payload["spec"].get("access_control_policy_list", []):
        _row["operation"] = "UPDATE"

        if _row["acp"]["name"] == acp_name:
            is_acp_present = True
            acp_resources = _row["acp"]["resources"]
            updated_user_reference_list = []
            updated_group_reference_list = []

            acp_users = []
            acp_groups = []
            for user in acp_resources.get("user_reference_list", []):
                acp_users.append(user["name"])

            for group in acp_resources.get("user_group_reference_list", []):
                acp_groups.append(group["name"])

            if not set(remove_user_list).issubset(set(acp_users)):
                LOG.error(
                    "Users {} are not registered in acp".format(
                        set(remove_user_list).difference(set(acp_users))
                    )
                )
                sys.exit(-1)

            if not set(remove_group_list).issubset(set(acp_groups)):
                LOG.error(
                    "Groups {} are not registered in acp".format(
                        set(remove_group_list).difference(set(acp_groups))
                    )
                )
                sys.exit(-1)

            for user in acp_resources.get("user_reference_list", []):
                if user["name"] not in remove_user_list:
                    updated_user_reference_list.append(user)

            for group in acp_resources.get("user_group_reference_list", []):
                if group["name"] not in remove_group_list:
                    updated_group_reference_list.append(group)

            # TODO check these users are not present in project's other acps
            user_name_uuid_map = client.user.get_name_uuid_map({"length": 1000})
            for user in add_user_list:
                updated_user_reference_list.append(
                    {"kind": "user", "name": user, "uuid": user_name_uuid_map[user]}
                )

            usergroup_name_uuid_map = client.group.get_name_uuid_map({"length": 1000})
            for group in add_group_list:
                updated_group_reference_list.append(
                    {
                        "kind": "user_group",
                        "name": group,
                        "uuid": usergroup_name_uuid_map[group],
                    }
                )

            acp_resources["user_reference_list"] = updated_user_reference_list
            acp_resources["user_group_reference_list"] = updated_group_reference_list

    if not is_acp_present:
        LOG.error(
            "No ACP with name '{}' exists in project '{}'".format(
                acp_name, project_name
            )
        )
        sys.exit(-1)

    LOG.info(
        "Updating acp '{}' associated with project '{}'".format(acp_name, project_name)
    )
    res, err = ProjectInternalObj.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    stdout_dict = {
        "name": acp_name,
        "execution_context": res["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))
    LOG.info("Polling on acp updation task")
    watch_task(res["status"]["execution_context"]["task_uuid"])
