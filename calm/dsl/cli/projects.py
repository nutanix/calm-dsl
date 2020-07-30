import time
import click
import arrow
import json
import sys
from prettytable import PrettyTable
from ruamel import yaml

from calm.dsl.builtins import ProjectValidator, create_project_payload, AhvProject
from calm.dsl.api import get_api_client
from calm.dsl.config import get_config

from .utils import get_name_query, get_module_from_file, highlight_text
from calm.dsl.log import get_logging_handle
from calm.dsl.providers import get_provider
from calm.dsl.store import Cache

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


def get_project(name):

    client = get_api_client()
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


def create_project(project_payload, name="", description=""):

    client = get_api_client()

    project_payload.pop("status", None)

    if name:
        project_payload["spec"]["name"] = name
        project_payload["metadata"]["name"] = name

    if description:
        project_payload["spec"]["description"] = description

    return client.project.create(project_payload)


def describe_project(project_name, out):

    client = get_api_client()
    project = get_project(project_name)

    if out == "json":
        project.pop("status", None)
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
        click.echo("\nRegistered Users: \n--------------------")
        for user in users:
            user_data = Cache.get_entity_data_using_uuid(
                entity_type="user", uuid=user["uuid"]
            )
            if not user_data:
                LOG.error(
                    "User ({}) details not present. Please update cache".format(
                        user["uuid"]
                    )
                )
                sys.exit(-1)
            click.echo("\t{}".format(highlight_text(user_data["name"])))

    groups = project_resources.get("external_user_group_reference_list", [])
    if groups:
        click.echo("\nRegistered Groups: \n--------------------")
        for group in groups:
            group_data = Cache.get_entity_data_using_uuid(
                entity_type="user_group", uuid=group["uuid"]
            )
            if not group_data:
                LOG.error(
                    "User Group ({}) details not present. Please update cache".format(
                        group["uuid"]
                    )
                )
                sys.exit(-1)
            click.echo("\t{}".format(highlight_text(group_data["name"])))

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
                ",_entity_id_==".join(subnets_list),
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
        click.echo("\nQuotas: \n-------\n")
        for qr in quota_resources:
            click.echo(
                "\t{} : {}".format(qr["resource_type"], highlight_text(qr["value"]))
            )


def delete_project(project_names):

    client = get_api_client()
    params = {"length": 1000}
    project_name_uuid_map = client.project.get_name_uuid_map(params)
    for project_name in project_names:
        project = get_project(project_name)
        project_id = project_name_uuid_map.get(project_name, "")
        if not project_id:
            LOG.warning("Project {} doesn't exist".format(project_name))
            continue

        res, err = client.project.delete(project_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        LOG.info("Project {} deleted".format(project_name))
