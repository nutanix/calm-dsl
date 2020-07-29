import time
import click
import arrow
import json
from prettytable import PrettyTable
from ruamel import yaml

from calm.dsl.builtins import ProjectValidator, create_project_payload, AhvProject
from calm.dsl.api import get_api_client
from calm.dsl.config import get_config

from .utils import get_name_query, get_module_from_file, highlight_text
from calm.dsl.log import get_logging_handle
from calm.dsl.providers import get_provider

LOG = get_logging_handle(__name__)


def get_projects(name, filter_by, limit, offset, quiet, out):
    """ Get the projects, optionally filtered by a string """

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

    # right now there is no support for filter by state of project

    if filter_query:
        params["filter"] = filter_query

    res, err = client.project.list(params=params)

    if err:
        pc_ip = config["SERVER"]["pc_ip"]
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

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["state"]),
                highlight_text(metadata["owner_reference"]["name"]),
                highlight_text(len(row["resources"]["user_reference_list"])),
                highlight_text(time.ctime(creation_time)),
                "{}".format(last_update_time.humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def get_project(client, name):

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

    project_id = project["metadata"]["uuid"]
    LOG.info("Fetching details of project {}".format(name))
    res, err = client.project.read(project_id)  # for getting additional fields
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    project = res.json()
    return project


def delete_project(project_names):

    client = get_api_client()

    for project_name in project_names:
        project = get_project(client, project_name)
        project_id = project["metadata"]["uuid"]
        res, err = client.project.delete(project_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Project {} deleted".format(project_name))


def get_project_module_from_file(project_file):
    """Returns Project module given a user project dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_project", project_file)


def get_project_class_from_module(user_project_module):
    """Returns project class given a module"""

    UserProject = None
    for item in dir(user_project_module):
        obj = getattr(user_project_module, item)
        if isinstance(obj, type(AhvProject)):
            if obj.__bases__[0] == AhvProject:
                UserProject = obj

    return UserProject


def compile_project(project_file):

    user_project_module = get_project_module_from_file(project_file)
    UserProject = get_project_class_from_module(user_project_module)
    if UserProject is None:
        return None

    project_payload = None
    UserProjectPayload, _ = create_project_payload(UserProject)
    project_payload = UserProjectPayload.get_dict()

    return project_payload


def create_project_using_dsl_payload(project_payload, name="", description=""):

    client = get_api_client()

    project_payload.pop("status", None)

    if name:
        project_payload["spec"]["name"] = name
        project_payload["metadata"]["name"] = name

    if description:
        project_payload["spec"]["description"] = description

    return client.project.create(project_payload)


def compile_project_command(project_file, out):

    project_payload = compile_project(project_file)
    if project_payload is None:
        LOG.error("User project not found in {}".format(project_file))
        return

    if out == "json":
        click.echo(json.dumps(project_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(project_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def create_project(payload):

    name = payload["project_detail"]["name"]
    client = get_api_client()

    # check if project having same name exists
    LOG.info("Searching for projects having same name ")
    params = {"filter": "name=={}".format(name)}
    res, err = client.project.list(params=params)
    if err:
        return None, err

    response = res.json()
    entities = response.get("entities", None)
    if entities:
        if len(entities) > 0:
            err_msg = "Project with name {} already exists".format(name)
            err = {"error": err_msg, "code": -1}
            return None, err

    LOG.info("Creating the project {}".format(name))

    # validating the payload
    ProjectValidator.validate_dict(payload)
    payload = {
        "api_version": "3.0",  # TODO Remove by a constant
        "metadata": {"kind": "project"},
        "spec": payload,
    }

    return client.project.create_internal(payload)


def describe_project(project_name, out):

    client = get_api_client()
    project = get_project(client, project_name)

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

    environments = project["status"]["project_status"]["resources"][
        "environment_reference_list"
    ]
    click.echo("Environment Registered: ", nl=False)

    if not environments:
        click.echo(highlight_text("No"))
    else:  # Handle Multiple Environments
        click.echo(
            "{} ( uuid: {} )".format(highlight_text("Yes"), environments[0]["uuid"])
        )

    acp_list = project["status"]["access_control_policy_list_status"]
    click.echo("\nUsers, Group and Roles: \n-----------------------\n")
    if not acp_list:
        click.echo(highlight_text("No users or groups registered\n"))

    else:
        for acp in acp_list:
            role = acp["access_control_policy_status"]["resources"]["role_reference"]
            users = acp["access_control_policy_status"]["resources"][
                "user_reference_list"
            ]
            groups = acp["access_control_policy_status"]["resources"][
                "user_group_reference_list"
            ]

            click.echo("Role: {}".format(highlight_text(role["name"])))

            if users:
                click.echo("Users: ")
                for index, user in enumerate(users):
                    name = user["name"].split("@")[0]
                    click.echo("\t{}. {}".format(str(index + 1), highlight_text(name)))

            if groups:
                click.echo("User Groups: ")
                for index, group in enumerate(groups):
                    name = group["name"].split(",")[0]
                    name = name.split("=")[1]
                    click.echo("\t{}. {}".format(str(index + 1), highlight_text(name)))

            click.echo("")

    click.echo("Infrastructure: \n---------------\n")

    accounts = project["status"]["project_status"]["resources"][
        "account_reference_list"
    ]
    payload = {"length": 200, "offset": 0, "filter": "state!=DELETED;type!=nutanix"}
    account_name_uuid_map = client.account.get_name_uuid_map(payload)
    account_uuid_name_map = {}
    # BUG: Same type of account have multiple uuids (Nutanix clusters)
    for k, v in account_name_uuid_map.items():
        if isinstance(v, list):
            for i in v:
                account_uuid_name_map[i] = k
        else:
            account_uuid_name_map[v] = k

    res, err = client.account.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    account_name_type_map = {}
    for entity in res["entities"]:
        name = entity["status"]["name"]
        account_type = entity["status"]["resources"]["type"]
        account_name_type_map[name] = account_type

    subnets_list = []
    for subnet in project["status"]["project_status"]["resources"][
        "subnet_reference_list"
    ]:
        subnets_list.append(subnet["uuid"])

    # Extending external subnet's list from remote account
    for subnet in project["status"]["project_status"]["resources"].get(
        "external_network_list", []
    ):
        subnets_list.append(subnet["uuid"])

    ntnx_pc_account_uuid = ""
    for account in accounts:
        account_uuid = account["uuid"]
        account_name = account_uuid_name_map[account_uuid]
        account_type = account_name_type_map[account_name]

        if account_type == "nutanix_pc":
            ntnx_pc_account_uuid = account_uuid
            continue

        click.echo("Account Type: " + highlight_text(account_type.upper()))
        click.echo(
            "Name: {} (uuid: {})\n".format(
                highlight_text(account_name), highlight_text(account_uuid)
            )
        )

    # Extracting subnets for nutanix accounts
    if subnets_list or ntnx_pc_account_uuid:
        if ntnx_pc_account_uuid:
            account_name = account_uuid_name_map[ntnx_pc_account_uuid]
            account_type = account_name_type_map[account_name]
            click.echo("Account Type: " + highlight_text(account_type.upper()))
            click.echo(
                "Name: {} (uuid: {})\n".format(
                    highlight_text(account_name), highlight_text(account_uuid)
                )
            )

        else:
            click.echo("Account Type: " + highlight_text("NUTANIX"))

        AhvVmProvider = get_provider("AHV_VM")
        AhvObj = AhvVmProvider.get_api_obj()

        filter_query = "(_entity_id_=={})".format(",_entity_id_==".join(subnets_list),)
        nics = AhvObj.subnets(
            account_uuid=ntnx_pc_account_uuid, filter_query=filter_query
        )
        nics = nics["entities"]

        if nics:
            click.echo("\tWhitelisted Subnets:\n\t--------------------")
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

    if not (subnets_list or accounts):
        click.echo(highlight_text("No provider's account registered"))

    click.echo("\nQuotas: \n-------\n")
    resources = project["status"]["project_status"]["resources"]

    if not resources.get("resource_domain"):
        click.echo(highlight_text("No quotas available"))
    else:
        resources = resources["resource_domain"]["resources"]
        for resource in resources:
            click.echo(
                "{} : {}".format(
                    resource["resource_type"], highlight_text(resource["value"])
                )
            )

        if not resources:
            click.echo(highlight_text("No quotas data provided"))

    click.echo("\n")


def update_project(name, payload):

    client = get_api_client()
    LOG.info("Searching for project")
    project = get_project(client, name)

    new_name = payload["project_detail"]["name"]
    if name != new_name:
        # Search whether any other project exists with new name
        LOG.info("\nSearching project with name {}".format(new_name))
        try:
            get_project(client, new_name)
            err_msg = "Another project exists with name {}".format(new_name)
            err = {"error": err_msg, "code": -1}
            return None, err

        except Exception:
            LOG.info("No project exists with name {}".format(new_name))

    project_id = project["metadata"]["uuid"]
    spec_version = project["metadata"]["spec_version"]
    ProjectValidator.validate_dict(payload)

    payload = {
        "api_version": "3.0",  # TODO Remove by a constant
        "metadata": {
            "kind": "project",
            "uuid": project_id,
            "spec_version": spec_version,
        },
        "spec": payload,
    }

    LOG.info("Updating the project")
    return client.project.update(project_id, payload)


def poll_creation_status(client, project_uuid):

    cnt = 0
    project_state = "PENDING"
    while True:
        LOG.info("Fetching status of project creation")
        res, err = client.project.read(project_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        project = res.json()
        project_state = project["status"]["state"]
        if project_state == "COMPLETE":
            LOG.info("CREATED")
            return

        elif project_state == "RUNNING":
            LOG.info("RUNNING")

        elif project_state == "PENDING":
            LOG.info("PENDING")

        else:
            msg = str(project["status"]["message_list"])
            msg = "Project creation unsuccessful !!!\nmessage={}".format(msg)
            raise Exception(msg)

        time.sleep(2)
        cnt += 1
        if cnt == 10:
            break

    LOG.debug("Waited for project creation for 20 seconds(polled at 2 sec interval).")
    LOG.info("Project state: {}".format(project_state))


def poll_updation_status(client, project_uuid, old_spec_version):

    cnt = 0
    project_state = "PENDING"
    while True:
        LOG.info("Fetching status of project updation")
        res, err = client.project.read(project_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        project = res.json()
        project_state = project["status"]["state"]
        spec_version = project["metadata"]["spec_version"]

        # On updation spec_version should be incremented
        if spec_version == old_spec_version:
            raise Exception("No update operation performed on project !!!")

        elif project_state == "PENDING":
            LOG.info("PENDING")

        elif project_state == "COMPLETE":
            LOG.info("UPDATED")
            return

        elif project_state == "RUNNING":
            LOG.info("RUNNING")

        else:
            msg = str(project["status"]["message_list"])
            msg = "Project updation failed !!!\nmessage={}".format(msg)
            raise Exception(msg)

        time.sleep(2)
        cnt += 1
        if cnt == 10:
            break

    LOG.debug("Waited for project updation for 20 seconds(polled at 2 sec interval)")
    LOG.info("Project state: {}".format(project_state))


def poll_deletion_status(client, project_uuid):

    cnt = 0
    project_state = "DELETE_IN_PROGRESS"
    while True:
        LOG.info("Fetching status of project deletion")
        res, err = client.project.read(project_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        project = res.json()
        project_state = project["status"]["state"]

        if project_state == "DELETE_IN_PROGRESS":
            LOG.info(project_state)

        elif project_state == "COMPLETE":
            LOG.info("DELETED")
            return

        elif project_state == "DELETE_PENDING":
            LOG.info(project_state)

        else:
            LOG.debug(project_state)
            msg = str(project["status"]["message_list"])
            msg = "Project updation failed !!!\nmessage={}".format(msg)
            raise Exception(msg)

        time.sleep(1)
        cnt += 2
        if cnt == 10:
            break

    LOG.debug("Waited for project deletion for 20 seconds(polled at 2 sec interval)")
    LOG.info("Project state: {}".format(project_state))
