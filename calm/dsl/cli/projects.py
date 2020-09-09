import time
import click
import arrow
import json
import sys
from prettytable import PrettyTable
from ruamel import yaml

from calm.dsl.builtins import create_project_payload, Project
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.config import get_context

from .utils import get_name_query, highlight_text
from .task_commands import watch_task
from .constants import ERGON_TASK
from .environments import create_environment_from_dsl_class
from calm.dsl.tools import get_module_from_file
from calm.dsl.log import get_logging_handle
from calm.dsl.providers import get_provider
from calm.dsl.store import Cache

LOG = get_logging_handle(__name__)


def get_projects(name, filter_by, limit, offset, quiet, out):
    """ Get the projects, optionally filtered by a string """

    client = get_api_client()
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    # right now there is no support for filter by state of project

    if filter_query:
        params["filter"] = filter_query

    res, err = client.project.list(params=params)

    if err:
        pc_ip = server_config["pc_ip"]
        LOG.warning("Cannot fetch projects from {}".format(pc_ip))
        return

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No project found !!!\n"))
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
        "OWNER",
        "USER COUNT",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        creation_time = arrow.get(metadata["creation_time"]).timestamp
        last_update_time = arrow.get(metadata["last_update_time"])
        if "owner_reference" in metadata:
            owner_reference_name = metadata["owner_reference"]["name"]
        else:
            owner_reference_name = "-"

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["state"]),
                highlight_text(owner_reference_name),
                highlight_text(len(row["resources"]["user_reference_list"])),
                highlight_text(time.ctime(creation_time)),
                "{}".format(last_update_time.humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def get_project(name=None, project_uuid=""):

    if not (name or project_uuid):
        LOG.error("One of name or uuid must be provided")
        sys.exit(-1)

    client = get_api_client()
    if not project_uuid:
        params = {"filter": "name=={}".format(name)}

        LOG.info("Searching for the project {}".format(name))
        res, err = client.project.list(params=params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities", None)
        project = None
        if entities:
            if len(entities) != 1:
                raise Exception("More than one project found - {}".format(entities))

            LOG.info("Project {} found ".format(name))
            project = entities[0]
        else:
            raise Exception("No project found with name {} found".format(name))

        project_uuid = project["metadata"]["uuid"]
        LOG.info("Fetching details of project {}".format(name))

    else:
        LOG.info("Fetching details of project (uuid='{}')".format(project_uuid))

    res, err = client.project.read(project_uuid)  # for getting additional fields
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    project = res.json()
    return project


def get_project_module_from_file(project_file):
    """Returns Project module given a user project dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_project", project_file)


def get_project_class_from_module(user_project_module):
    """Returns project class given a module"""

    UserProject = None
    for item in dir(user_project_module):
        obj = getattr(user_project_module, item)
        if isinstance(obj, type(Project)):
            if obj.__bases__[0] == Project:
                UserProject = obj

    return UserProject


def compile_project_dsl_class(project_class):

    project_payload = None
    UserProjectPayload, _ = create_project_payload(project_class)
    project_payload = UserProjectPayload.get_dict()

    return project_payload


def compile_project_command(project_file, out):

    user_project_module = get_project_module_from_file(project_file)
    UserProject = get_project_class_from_module(user_project_module)
    if UserProject is None:
        LOG.error("User project not found in {}".format(project_file))
        return

    # Environment definitions are not part of project
    if hasattr(UserProject, "envs"):
        UserProject.envs = []

    project_payload = compile_project_dsl_class(UserProject)

    if out == "json":
        click.echo(json.dumps(project_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(project_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def create_project(project_payload, name="", description=""):

    client = get_api_client()

    project_payload.pop("status", None)

    if name:
        project_payload["spec"]["name"] = name
        project_payload["metadata"]["name"] = name
    else:
        name = project_payload["spec"]["name"]

    if description:
        project_payload["spec"]["description"] = description

    LOG.info("Creating project '{}'".format(name))
    res, err = client.project.create(project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project = res.json()
    stdout_dict = {
        "name": project["metadata"]["name"],
        "uuid": project["metadata"]["uuid"],
        "execution_context": project["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    LOG.info("Polling on project creation task")
    task_state = watch_task(project["status"]["execution_context"]["task_uuid"])
    if task_state in ERGON_TASK.FAILURE_STATES:
        raise Exception("Project creation task went to {} state".format(task_state))

    return stdout_dict


def update_project(project_uuid, project_payload):

    client = get_api_client()

    project_payload.pop("status", None)
    res, err = client.project.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project = res.json()
    stdout_dict = {
        "name": project["metadata"]["name"],
        "uuid": project["metadata"]["uuid"],
        "execution_context": project["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    LOG.info("Polling on project updation task")
    task_state = watch_task(project["status"]["execution_context"]["task_uuid"])
    if task_state in ERGON_TASK.FAILURE_STATES:
        raise Exception("Project creation task went to {} state".format(task_state))

    return stdout_dict


def create_project_from_dsl(project_file, project_name, description=""):
    """Steps:
    1. Creation of project without env
    2. Creation of env
    3. Updation of project for adding env details
    """

    client = get_api_client()

    user_project_module = get_project_module_from_file(project_file)
    UserProject = get_project_class_from_module(user_project_module)
    if UserProject is None:
        LOG.error("User project not found in {}".format(project_file))
        return

    envs = []
    if hasattr(UserProject, "envs"):
        envs = getattr(UserProject, "envs", [])
        UserProject.envs = []

    if len(envs) > 1:
        LOG.error("Multiple environments in a project are not allowed.")
        sys.exit(-1)

    for _env in envs:
        env_name = _env.__name__
        LOG.info("Searching for existing environments with name '{}'".format(env_name))
        res, err = client.environment.list({"filter": "name=={}".format(env_name)})
        if err:
            LOG.error(err)
            sys.exit(-1)

        res = res.json()
        if res["metadata"]["total_matches"]:
            LOG.error("Environment with name '{}' already exists".format(env_name))
            sys.exit(-1)

        LOG.info("No existing environment found with name '{}'".format(env_name))

    # Creation of project
    project_payload = compile_project_dsl_class(UserProject)
    project_data = create_project(
        project_payload, name=project_name, description=description
    )
    project_name = project_data["name"]
    project_uuid = project_data["uuid"]

    if envs:
        # Update project in cache
        Cache.sync_table("project")

        # As ahv helpers in environment should use account from project accounts
        # updating the context
        ContextObj = get_context()
        ContextObj.update_project_context(project_name=project_name)

        # Create environment
        env_ref_list = []
        for env_obj in envs:
            env_res_data = create_environment_from_dsl_class(env_obj)
            env_ref_list.append({"kind": "environment", "uuid": env_res_data["uuid"]})

        LOG.info("Updating project '{}' for adding environment".format(project_name))
        project_payload = get_project(project_uuid=project_uuid)

        # NOTE Single environment is supported. So not extending existing list
        project_payload.pop("status", None)
        project_payload["spec"]["resources"][
            "environment_reference_list"
        ] = env_ref_list

        update_project(project_uuid=project_uuid, project_payload=project_payload)


def describe_project(project_name, out):

    client = get_api_client()
    project = get_project(project_name)

    if out == "json":
        click.echo(json.dumps(project, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Project Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(project_name)
        + " (uuid: "
        + highlight_text(project["metadata"]["uuid"])
        + ")"
    )

    click.echo("Status: " + highlight_text(project["status"]["state"]))
    click.echo(
        "Owner: " + highlight_text(project["metadata"]["owner_reference"]["name"])
    )

    created_on = arrow.get(project["metadata"]["creation_time"])
    past = created_on.humanize()
    click.echo(
        "Created on: {} ({})".format(
            highlight_text(time.ctime(created_on.timestamp)), highlight_text(past)
        )
    )

    project_resources = project["status"].get("resources", {})
    environments = project_resources.get("environment_reference_list", [])
    click.echo("Environment Registered: ", nl=False)

    if not environments:
        click.echo(highlight_text("No"))
    else:  # Handle Multiple Environments
        click.echo(
            "{} ( uuid: {} )".format(highlight_text("Yes"), environments[0]["uuid"])
        )

    users = project_resources.get("user_reference_list", [])
    if users:
        user_uuid_name_map = client.user.get_uuid_name_map({"length": 1000})
        click.echo("\nRegistered Users: \n--------------------")
        for user in users:
            click.echo("\t" + highlight_text(user_uuid_name_map[user["uuid"]]))

    groups = project_resources.get("external_user_group_reference_list", [])
    if groups:
        usergroup_uuid_name_map = client.group.get_uuid_name_map({"length": 1000})
        click.echo("\nRegistered Groups: \n--------------------")
        for group in groups:
            click.echo("\t" + highlight_text(usergroup_uuid_name_map[group["uuid"]]))

    click.echo("\nInfrastructure: \n---------------")

    subnets_list = []
    for subnet in project_resources["subnet_reference_list"]:
        subnets_list.append(subnet["uuid"])

    # Extending external subnet's list from remote account
    for subnet in project_resources.get("external_network_list", []):
        subnets_list.append(subnet["uuid"])

    accounts = project_resources["account_reference_list"]
    for account in accounts:
        account_uuid = account["uuid"]
        account_cache_data = Cache.get_entity_data_using_uuid(
            entity_type="account", uuid=account_uuid
        )
        if not account_cache_data:
            LOG.error(
                "Account (uuid={}) not found. Please update cache".format(account_uuid)
            )
            sys.exit(-1)

        account_type = account_cache_data["provider_type"]
        click.echo("\nAccount Type: " + highlight_text(account_type.upper()))
        click.echo(
            "Name: {} (uuid: {})".format(
                highlight_text(account_cache_data["name"]),
                highlight_text(account_cache_data["uuid"]),
            )
        )

        if account_type == "nutanix_pc" and subnets_list:
            AhvVmProvider = get_provider("AHV_VM")
            AhvObj = AhvVmProvider.get_api_obj()

            filter_query = "(_entity_id_=={})".format(
                ",_entity_id_==".join(subnets_list)
            )
            nics = AhvObj.subnets(account_uuid=account_uuid, filter_query=filter_query)
            nics = nics["entities"]

            click.echo("\n\tWhitelisted Subnets:\n\t--------------------")
            for nic in nics:
                nic_name = nic["status"]["name"]
                vlan_id = nic["status"]["resources"]["vlan_id"]
                cluster_name = nic["status"]["cluster_reference"]["name"]
                nic_uuid = nic["metadata"]["uuid"]

                click.echo(
                    "\tName: {} (uuid: {})\tVLAN ID: {}\tCluster Name: {}".format(
                        highlight_text(nic_name),
                        highlight_text(nic_uuid),
                        highlight_text(vlan_id),
                        highlight_text(cluster_name),
                    )
                )

    if not accounts:
        click.echo(highlight_text("No provider's account registered"))

    quota_resources = project_resources.get("resource_domain", {}).get("resources", [])
    if quota_resources:
        click.echo("\nQuotas: \n-------")
        for qr in quota_resources:
            qk = qr["resource_type"]
            qv = qr["limit"]
            if qr["units"] == "BYTES":
                qv = qv // 1073741824
                qv = str(qv) + " (GiB)"

            click.echo("\t{} : {}".format(qk, highlight_text(qv)))


def delete_project(project_names):

    client = get_api_client()
    params = {"length": 1000}
    project_name_uuid_map = client.project.get_name_uuid_map(params)
    for project_name in project_names:
        project_id = project_name_uuid_map.get(project_name, "")
        if not project_id:
            LOG.warning("Project {} not found.".format(project_name))
            continue

        LOG.info("Deleting project '{}'".format(project_name))
        res, err = client.project.delete(project_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Polling on project deletion task")
        res = res.json()
        task_state = watch_task(res["status"]["execution_context"]["task_uuid"])
        if task_state in ERGON_TASK.FAILURE_STATES:
            raise Exception("Project deletion task went to {} state".format(task_state))
        click.echo("")


def update_project_from_dsl(project_name, project_file):

    client = get_api_client()

    user_project_module = get_project_module_from_file(project_file)
    UserProject = get_project_class_from_module(user_project_module)
    if UserProject is None:
        LOG.error("User project not found in {}".format(project_file))
        return

    # Environment updation is not allowed using dsl file
    if hasattr(UserProject, "envs"):
        UserProject.envs = []

    project_payload = compile_project_dsl_class(UserProject)

    LOG.info("Fetching project '{}' details".format(project_name))
    params = {"length": 1000, "filter": "name=={}".format(project_name)}
    project_name_uuid_map = client.project.get_name_uuid_map(params)
    project_uuid = project_name_uuid_map.get(project_name, "")

    if not project_uuid:
        LOG.error("Project {} not found.".format(project_name))
        sys.exit(-1)

    res, err = client.project.read(project_uuid)
    if err:
        LOG.error(err)
        sys.exit(-1)

    old_project_payload = res.json()

    # Find users already registered
    updated_project_user_list = []
    for _user in project_payload["spec"]["resources"].get("user_reference_list", []):
        updated_project_user_list.append(_user["name"])

    updated_project_groups_list = []
    for _group in project_payload["spec"]["resources"].get(
        "external_user_group_reference_list", []
    ):
        updated_project_groups_list.append(_group["name"])

    acp_remove_user_list = []
    acp_remove_group_list = []
    for _user in old_project_payload["spec"]["resources"].get(
        "user_reference_list", []
    ):
        if _user["name"] not in updated_project_user_list:
            acp_remove_user_list.append(_user["name"])

    for _group in old_project_payload["spec"]["resources"].get(
        "external_user_group_reference_list", []
    ):
        if _group["name"] not in updated_project_groups_list:
            acp_remove_group_list.append(_group["name"])

    # Setting correct metadata for update call
    project_payload["metadata"] = old_project_payload["metadata"]

    # As name of project is not editable
    project_payload["spec"]["name"] = project_name
    project_payload["metadata"]["name"] = project_name

    # TODO removed users should be removed from acps also.
    LOG.info("Updating project '{}'".format(project_name))
    res, err = client.project.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    stdout_dict = {
        "name": res["metadata"]["name"],
        "uuid": res["metadata"]["uuid"],
        "execution_context": res["status"]["execution_context"],
    }

    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    LOG.info("Polling on project creation task")
    task_state = watch_task(res["status"]["execution_context"]["task_uuid"])
    if task_state not in ERGON_TASK.FAILURE_STATES:
        # Remove project removed user and groups from acps
        if acp_remove_user_list or acp_remove_group_list:
            LOG.info("Updating project acps")
            remove_users_from_project_acps(
                project_uuid=project_uuid,
                remove_user_list=acp_remove_user_list,
                remove_group_list=acp_remove_group_list,
            )
    else:
        raise Exception("Project updation task went to {} state".format(task_state))


def update_project_using_cli_switches(
    project_name, add_user_list, add_group_list, remove_user_list, remove_group_list
):

    client = get_api_client()

    LOG.info("Fetching project '{}' details".format(project_name))
    params = {"length": 1000, "filter": "name=={}".format(project_name)}
    project_name_uuid_map = client.project.get_name_uuid_map(params)
    project_uuid = project_name_uuid_map.get(project_name, "")

    if not project_uuid:
        LOG.error("Project {} not found.".format(project_name))
        sys.exit(-1)

    res, err = client.project.read(project_uuid)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project_payload = res.json()
    project_payload.pop("status", None)

    project_resources = project_payload["spec"]["resources"]
    project_users = []
    project_groups = []
    for user in project_resources.get("user_reference_list", []):
        project_users.append(user["name"])

    for group in project_resources.get("external_user_group_reference_list", []):
        project_groups.append(group["name"])

    # Checking remove users/groups are part of project or not
    if not set(remove_user_list).issubset(set(project_users)):
        LOG.error(
            "Users {} are not registered in project".format(
                set(remove_user_list).difference(set(project_users))
            )
        )
        sys.exit(-1)

    if not set(remove_group_list).issubset(set(project_groups)):
        LOG.error(
            "Groups {} are not registered in project".format(
                set(remove_group_list).difference(set(project_groups))
            )
        )
        sys.exit(-1)

    # Append users
    updated_user_reference_list = []
    updated_group_reference_list = []

    acp_remove_user_list = []
    acp_remove_group_list = []

    for user in project_resources.get("user_reference_list", []):
        if user["name"] not in remove_user_list:
            updated_user_reference_list.append(user)
        else:
            acp_remove_user_list.append(user["name"])

    for group in project_resources.get("external_user_group_reference_list", []):
        if group["name"] not in remove_group_list:
            updated_group_reference_list.append(group)
        else:
            acp_remove_group_list.append(group["name"])

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

    project_resources["user_reference_list"] = updated_user_reference_list
    project_resources[
        "external_user_group_reference_list"
    ] = updated_group_reference_list

    LOG.info("Updating project '{}'".format(project_name))
    res, err = client.project.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    stdout_dict = {
        "name": res["metadata"]["name"],
        "uuid": res["metadata"]["uuid"],
        "execution_context": res["status"]["execution_context"],
    }

    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    # Remove project removed user and groups from acps
    LOG.info("Polling on project updation task")
    task_state = watch_task(res["status"]["execution_context"]["task_uuid"])
    if task_state not in ERGON_TASK.FAILURE_STATES:
        if acp_remove_user_list or acp_remove_group_list:
            LOG.info("Updating project acps")
            remove_users_from_project_acps(
                project_uuid=project_uuid,
                remove_user_list=acp_remove_user_list,
                remove_group_list=acp_remove_group_list,
            )
    else:
        raise Exception("Project updation task went to {} state".format(task_state))


def remove_users_from_project_acps(project_uuid, remove_user_list, remove_group_list):

    client = get_api_client()
    ProjectInternalObj = get_resource_api("projects_internal", client.connection)
    res, err = ProjectInternalObj.read(project_uuid)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project_payload = res.json()
    project_payload.pop("status", None)

    for _acp in project_payload["spec"].get("access_control_policy_list", []):
        _acp["operation"] = "UPDATE"
        _acp_resources = _acp["acp"]["resources"]
        updated_users = []
        updated_groups = []

        for _user in _acp_resources.get("user_reference_list", []):
            if _user["name"] not in remove_user_list:
                updated_users.append(_user)

        for _group in _acp_resources.get("user_group_reference_list", []):
            if _group["name"] not in remove_group_list:
                updated_groups.append(_group)

        _acp_resources["user_reference_list"] = updated_users
        _acp_resources["user_group_reference_list"] = updated_groups

    res, err = ProjectInternalObj.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    LOG.info("Polling on task for updating project ACPS")
    watch_task(res["status"]["execution_context"]["task_uuid"])
