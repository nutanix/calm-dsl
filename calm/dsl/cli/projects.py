from inspect import getargs
import time
import click
import arrow
import json
import sys
import copy
from distutils.version import LooseVersion as LV
from prettytable import PrettyTable
from ruamel import yaml

from calm.dsl.builtins import create_project_payload, Project
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.config import get_context

from .utils import get_name_query, highlight_text
from .environments import create_environment_from_dsl_class
from calm.dsl.tools import get_module_from_file
from calm.dsl.log import get_logging_handle
from calm.dsl.providers import get_provider
from calm.dsl.builtins.models.helper.common import get_project
from calm.dsl.cli.quotas import (
    _set_quota_state,
    get_quota_uuid_at_project,
    create_quota_at_project,
    set_quota_at_project,
)
from calm.dsl.store import Cache, Version
from calm.dsl.constants import CACHE, PROJECT_TASK, QUOTA

LOG = get_logging_handle(__name__)


def get_projects(name, filter_by, limit, offset, quiet, out):
    """Get the projects, optionally filtered by a string"""

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


def watch_project_task(project_uuid, task_uuid, poll_interval=4):
    """poll project tasks"""

    client = get_api_client()
    cnt = 0
    while True:
        LOG.info("Fetching status of project task (uuid={})".format(task_uuid))
        res, err = client.project.read_pending_task(project_uuid, task_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        status = res["status"]["state"]
        LOG.info(status)

        if status in PROJECT_TASK.TERMINAL_STATES:
            message_list = res["status"].get("message_list")
            if status != PROJECT_TASK.STATUS.SUCCESS and message_list:
                LOG.error(message_list)
            return status

        time.sleep(poll_interval)
        cnt += 1
        if cnt == 10:
            break

    LOG.info(
        "Task couldn't reached to terminal state in {} seconds. Exiting...".format(
            poll_interval * 10
        )
    )


def convert_groups_to_lowercase(group_list):
    group_mutable_list = []
    for group in group_list:
        group_mutable_list.append(group.lower())
    group_list = tuple(group_mutable_list)
    return group_list


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
    envs = []
    if hasattr(project_class, "envs"):
        envs = getattr(project_class, "envs", [])
        project_class.envs = []
        if hasattr(project_class, "default_environment"):
            project_class.default_environment = {}

    # Adding environment infra to project
    for env in envs:
        providers = getattr(env, "providers", [])
        for env_pdr in providers:
            env_pdr_account = env_pdr.account_reference.get_dict()
            _a_found = False
            for proj_pdr in getattr(project_class, "providers", []):
                proj_pdr_account = proj_pdr.account_reference.get_dict()
                if env_pdr_account["name"] == proj_pdr_account["name"]:
                    _a_found = True

                    # If env account subnets not present in project, then add them by default
                    if proj_pdr.type == "nutanix_pc":
                        env_pdr_subnets = env_pdr.subnet_reference_list
                        env_pdr_ext_subnets = env_pdr.external_network_list

                        proj_pdr_subnets = proj_pdr.subnet_reference_list
                        proj_pdr_ext_subnets = proj_pdr.external_network_list

                        for _s in env_pdr_subnets:
                            _s_uuid = _s.get_dict()["uuid"]
                            _s_found = False

                            for _ps in proj_pdr_subnets:
                                if _ps.get_dict()["uuid"] == _s_uuid:
                                    _s_found = True
                                    break

                            if not _s_found:
                                proj_pdr.subnet_reference_list.append(_s)

                        for _s in env_pdr_ext_subnets:
                            _s_uuid = _s.get_dict()["uuid"]
                            _s_found = False

                            for _ps in proj_pdr_ext_subnets:
                                if _ps.get_dict()["uuid"] == _s_uuid:
                                    _s_found = True
                                    break

                            if not _s_found:
                                proj_pdr.external_network_list.append(_s)

            # If environment account not available in project add it to project
            if not _a_found:
                project_class.providers.append(env_pdr)

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

    project_payload = compile_project_dsl_class(UserProject)

    if out == "json":
        click.echo(json.dumps(project_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(project_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def set_quota_at_project_level(client, quota, project_uuid):
    """Setting quota at project level"""

    quota_entities = {"project": project_uuid}

    res, err = _set_quota_state(
        client=client, state=QUOTA.STATE.ENABLED, quota_entities=quota_entities
    )

    if not res:
        LOG.exception("Setting quota state failed with error {}".format(err))
        sys.exit(-1)

    quota_uuid, _ = get_quota_uuid_at_project(
        client=client, quota_entities=quota_entities
    )

    if not quota_uuid:
        res, err = create_quota_at_project(
            client=client,
            quota=quota,
            project_uuid=project_uuid,
            quota_entities=quota_entities,
        )

        if res is None:
            LOG.exception("Quota creation at project failed with error {}".format(err))
            sys.exit(-1)
    else:
        res, err = set_quota_at_project(
            client=client,
            quota_uuid=quota_uuid,
            project_uuid=project_uuid,
            quota=quota,
            quota_entities=quota_entities,
        )
        if res is None:
            LOG.exception("Setting quota at project failed with error {}".format(err))
            sys.exit(-1)


def create_project(project_payload, name="", description=""):

    client = get_api_client()
    context_obj = get_context()

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
        "name": project["spec"]["name"],
        "uuid": project["metadata"]["uuid"],
        "execution_context": project["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    LOG.info("Polling on project creation task")
    task_state = watch_project_task(
        project["metadata"]["uuid"],
        project["status"]["execution_context"]["task_uuid"],
        poll_interval=4,
    )
    if task_state in PROJECT_TASK.FAILURE_STATES:
        LOG.exception("Project creation task went to {} state".format(task_state))
        sys.exit(-1)

    project_uuid = project["metadata"]["uuid"]

    quota = (
        project_payload.get("spec", {}).get("resources", {}).get("resource_domain", {})
    )

    if quota:
        policy_config = context_obj.get_policy_config()

        if policy_config.get("policy_status", "False") == "False":
            LOG.info("Quotas would not be set as policy is not enabled")
        else:
            set_quota_at_project_level(client, quota, project_uuid)

    return stdout_dict


def update_project(project_uuid, project_payload):

    client = get_api_client()
    calm_version = Version.get_version("Calm")

    project_payload.pop("status", None)
    res, err = client.project.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project = res.json()
    if LV(calm_version) >= LV("3.5.2") and LV(calm_version) < LV("3.6.1"):
        project_name = project["spec"]["project_detail"]["name"]
    else:
        project_name = project["spec"]["name"]
    stdout_dict = {
        "name": project_name,
        "uuid": project["metadata"]["uuid"],
        "execution_context": project["status"]["execution_context"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    LOG.info("Polling on project updation task")
    task_state = watch_project_task(
        project["metadata"]["uuid"], project["status"]["execution_context"]["task_uuid"]
    )
    if task_state in PROJECT_TASK.FAILURE_STATES:
        LOG.exception("Project updation task went to {} state".format(task_state))
        sys.exit(-1)

    return stdout_dict


def create_project_from_dsl(
    project_file, project_name, description="", no_cache_update=False
):
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

    default_environment_name = ""
    if (
        hasattr(UserProject, "default_environment")
        and UserProject.default_environment is not None
    ):
        default_environment = getattr(UserProject, "default_environment", None)
        UserProject.default_environment = {}
        default_environment_name = default_environment.__name__

    if envs and not default_environment_name:
        default_environment_name = envs[0].__name__

    calm_version = Version.get_version("Calm")
    if LV(calm_version) < LV("3.2.0"):
        for _env in envs:
            env_name = _env.__name__
            LOG.info(
                "Searching for existing environments with name '{}'".format(env_name)
            )
            res, err = client.environment.list({"filter": "name=={}".format(env_name)})
            if err:
                LOG.error(err)
                sys.exit(-1)

            res = res.json()
            if res["metadata"]["total_matches"]:
                LOG.error("Environment with name '{}' already exists".format(env_name))

            LOG.info("No existing environment found with name '{}'".format(env_name))

    if envs and no_cache_update:
        LOG.error("Environment create is not allowed when cache update is disabled")
        return

    # Creation of project
    project_payload = compile_project_dsl_class(UserProject)
    project_data = create_project(
        project_payload, name=project_name, description=description
    )
    project_name = project_data["name"]
    project_uuid = project_data["uuid"]

    # Update project in cache
    LOG.info("Updating projects cache")
    Cache.add_one(entity_type=CACHE.ENTITY.PROJECT, uuid=project_uuid)
    LOG.info("[Done]")

    if envs:

        # As ahv helpers in environment should use account from project accounts
        # updating the context
        ContextObj = get_context()
        ContextObj.update_project_context(project_name=project_name)

        default_environment_ref = {}

        # Create environment
        env_ref_list = []
        for env_obj in envs:
            env_res_data = create_environment_from_dsl_class(env_obj)
            env_ref = {"kind": "environment", "uuid": env_res_data["uuid"]}
            env_ref_list.append(env_ref)
            if (
                default_environment_name
                and env_res_data["name"] == default_environment_name
            ):
                default_environment_ref = env_ref

        LOG.info("Updating project '{}' for adding environment".format(project_name))
        project_payload = get_project(project_uuid=project_uuid)

        project_payload.pop("status", None)
        project_payload["spec"]["resources"][
            "environment_reference_list"
        ] = env_ref_list

        default_environment_ref = default_environment_ref or {
            "kind": "environment",
            "uuid": env_ref_list[0]["uuid"],
        }

        # default_environment_reference added in 3.2
        calm_version = Version.get_version("Calm")
        if LV(calm_version) >= LV("3.2.0"):
            project_payload["spec"]["resources"][
                "default_environment_reference"
            ] = default_environment_ref

        update_project(project_uuid=project_uuid, project_payload=project_payload)

        # Reset the context changes
        ContextObj.reset_configuration()

        if no_cache_update:
            LOG.info("Skipping environments cache update")
        else:
            # Update environments in cache
            LOG.info("Updating environments cache ...")
            for _e_item in env_ref_list:
                Cache.add_one(
                    entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=_e_item["uuid"]
                )
            LOG.info("[Done]")


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

    clusters_list = []
    for cluster in project_resources.get("cluster_reference_list", []):
        clusters_list.append(cluster["uuid"])

    vpcs_list = []
    for vpc in project_resources.get("vpc_reference_list", []):
        vpcs_list.append(vpc["uuid"])

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

            filter_query = "_entity_id_=={}".format("|".join(subnets_list))
            nics = AhvObj.subnets(account_uuid=account_uuid, filter_query=filter_query)
            nics = nics["entities"]

            # passing entity ids in filter doesn't work for clusters list call
            clusters = AhvObj.clusters(account_uuid=account_uuid).get("entities", [])
            vpcs = AhvObj.vpcs(account_uuid=account_uuid).get("entities", [])

            vpc_uuid_name_map = {}

            click.echo("\n\tWhitelisted Clusters:\n\t--------------------")
            for cluster in clusters:
                if cluster["metadata"]["uuid"] in clusters_list:
                    click.echo(
                        "\tName: {} (uuid: {})".format(
                            highlight_text(cluster["status"]["name"]),
                            highlight_text(cluster["metadata"]["uuid"]),
                        )
                    )

            click.echo("\n\tWhitelited VPCs:\n\t--------------------")
            for vpc in vpcs:
                if vpc["metadata"]["uuid"] in vpcs_list:
                    vpc_name = vpc["status"]["name"]
                    click.echo(
                        "\tName: {} (uuid: {})".format(
                            highlight_text(vpc_name),
                            highlight_text(vpc["metadata"]["uuid"]),
                        )
                    )
                    vpc_uuid_name_map[vpc["metadata"]["uuid"]] = vpc_name

            click.echo("\n\tWhitelisted Subnets:\n\t--------------------")
            overlay_nics = []
            for nic in nics:
                if nic["status"]["resources"].get("subnet_type", "") != "VLAN":
                    overlay_nics.append(nic)
                    continue

                nic_name = nic["status"]["name"]
                vlan_id = nic["status"]["resources"]["vlan_id"]
                cluster_name = nic["status"]["cluster_reference"]["name"]
                nic_uuid = nic["metadata"]["uuid"]

                click.echo(
                    "\tName: {} (uuid: {})\tType: VLAN\tVLAN ID: {}\tCluster Name: {}".format(
                        highlight_text(nic_name),
                        highlight_text(nic_uuid),
                        highlight_text(vlan_id),
                        highlight_text(cluster_name),
                    )
                )
            for nic in overlay_nics:
                nic_name = nic["status"]["name"]
                nic_uuid = nic["metadata"]["uuid"]
                vpc_name = vpc_uuid_name_map.get(
                    nic["status"]["resources"]["vpc_reference"]["uuid"], ""
                )
                if vpc_name:
                    click.echo(
                        "\tName: {} (uuid: {})\tType: Overlay\tVPC Name: {}".format(
                            highlight_text(nic_name),
                            highlight_text(nic_uuid),
                            highlight_text(vpc_name),
                        )
                    )
                else:
                    click.echo(
                        "\tName: {} (uuid: {})\tType: Overlay".format(
                            highlight_text(nic_name),
                            highlight_text(nic_uuid),
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


def delete_project(project_names, no_cache_update=False):

    client = get_api_client()
    project_name_uuid_map = client.project.get_name_uuid_map()
    deleted_projects_uuids = []
    for project_name in project_names:
        project_id = project_name_uuid_map.get(project_name, "")
        if not project_id:
            LOG.warning("Project {} not found.".format(project_name))
            continue

        LOG.info("Deleting project '{}'".format(project_name))
        res, err = client.project.delete(project_id)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            continue

        deleted_projects_uuids.append(project_id)

        LOG.info("Polling on project deletion task")
        res = res.json()
        task_state = watch_project_task(
            project_id, res["status"]["execution_context"]["task_uuid"], poll_interval=4
        )
        if task_state in PROJECT_TASK.FAILURE_STATES:
            LOG.exception("Project deletion task went to {} state".format(task_state))
            sys.exit(-1)

    # Update projects in cache if any project has been deleted
    if deleted_projects_uuids:
        if no_cache_update:
            LOG.info("skipping projects cache update")
        else:
            LOG.info("Updating projects cache ...")
            for _proj_id in deleted_projects_uuids:
                Cache.delete_one(entity_type=CACHE.ENTITY.PROJECT, uuid=_proj_id)
            LOG.info("[Done]")


def update_project_from_dsl(
    project_name, project_file, no_cache_update=False, append_only=False
):
    """
    Flow:
        1. compile to get project_payload from the file
        2. If apppend_only, then update using old project data
        3. Calculate the data for acp updations
        4. If not append only, then do project_usage calculation
        5. Update project: PUT call
        6. If project is updated successfully, then do acp updations
    """

    client = get_api_client()
    context_obj = get_context()
    calm_version = Version.get_version("Calm")

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
    params = {"length": 250, "filter": "name=={}".format(project_name)}
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

    if append_only:
        update_payload_from_old_project_data(
            project_payload, copy.deepcopy(old_project_payload)
        )

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

    # Environment updation is not allowed, so adding existing environments
    old_env_refs = old_project_payload["spec"]["resources"].get(
        "environment_reference_list", []
    )
    if old_env_refs:
        project_payload["spec"]["resources"][
            "environment_reference_list"
        ] = old_env_refs

    default_env_ref = old_project_payload["spec"]["resources"].get(
        "default_environment_reference", {}
    )
    if default_env_ref:
        project_payload["spec"]["resources"][
            "default_environment_reference"
        ] = default_env_ref

    if not append_only:
        project_usage_payload = get_project_usage_payload(
            project_payload, old_project_payload
        )

        LOG.info("Checking project usage")
        res, err = client.project.usage(project_uuid, project_usage_payload)

        if err:
            LOG.error(err)
            sys.exit(-1)

        project_usage = res.json()
        msg_list = []
        should_update_project = is_project_updation_allowed(project_usage, msg_list)
        if not should_update_project:
            LOG.error("Project updation failed")
            click.echo("\n".join(msg_list))
            click.echo(
                json.dumps(
                    project_usage["status"].get("resources", {}),
                    indent=4,
                    separators=(",", ": "),
                )
            )
            sys.exit(-1)

    # Setting correct metadata for update call
    project_payload["metadata"] = old_project_payload["metadata"]

    # As name of project is not editable
    project_payload["spec"]["name"] = project_name
    project_payload["metadata"]["name"] = project_name

    # TODO removed users should be removed from acps also.
    LOG.info("Updating project '{}'".format(project_name))
    quota = (
        project_payload.get("spec", {}).get("resources", {}).get("resource_domain", {})
    )

    if quota:
        policy_config = context_obj.get_policy_config()

        if policy_config.get("policy_status", "False") == "False":
            LOG.info("Quotas would not be set as policy is not enabled")
        else:
            set_quota_at_project_level(client, quota, project_uuid)
    else:
        LOG.info(
            "Quotas not provided in the file, so already existing quotas will not be updated"
        )

    res, err = client.project.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    if LV(calm_version) >= LV("3.5.2") and LV(calm_version) < LV("3.6.1"):
        name = res["spec"]["project_detail"]["name"]
    else:
        name = res["spec"]["name"]

    stdout_dict = {
        "name": name,
        "uuid": res["metadata"]["uuid"],
        "execution_context": res["status"]["execution_context"],
    }

    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    LOG.info("Polling on project updation task")
    task_state = watch_project_task(
        project_uuid, res["status"]["execution_context"]["task_uuid"], poll_interval=4
    )
    if task_state not in PROJECT_TASK.FAILURE_STATES:
        # Remove project removed user and groups from acps
        if acp_remove_user_list or acp_remove_group_list:
            LOG.info("Updating project acps")
            remove_users_from_project_acps(
                project_uuid=project_uuid,
                remove_user_list=acp_remove_user_list,
                remove_group_list=acp_remove_group_list,
            )
    else:
        LOG.exception("Project updation task went to {} state".format(task_state))
        sys.exit(-1)

    if no_cache_update:
        LOG.info("Skipping projects cache update")
    else:
        LOG.info("Updating projects cache ...")
        Cache.update_one(entity_type=CACHE.ENTITY.PROJECT, uuid=project_uuid)
        LOG.info("[Done]")


def update_project_using_cli_switches(
    project_name,
    add_user_list,
    add_group_list,
    add_account_list,
    remove_account_list,
    remove_user_list,
    remove_group_list,
    disable_quotas,
    enable_quotas,
):

    client = get_api_client()
    calm_version = Version.get_version("Calm")

    LOG.info("Fetching project '{}' details".format(project_name))
    params = {"length": 250, "filter": "name=={}".format(project_name)}
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

    project_usage_payload = {
        "filter": {"account_reference_list": [], "subnet_reference_list": []}
    }
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

    remove_group_list = convert_groups_to_lowercase(remove_group_list)
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

    add_group_list = convert_groups_to_lowercase(add_group_list)
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

    # Updating accounts data
    if not set(add_account_list).isdisjoint(set(remove_account_list)):
        LOG.error(
            "Same accounts found in both added and removing list {}".format(
                set(add_account_list).intersection(set(remove_account_list))
            )
        )
        sys.exit("Same accounts found in both added and removing list")

    project_accounts = project_resources.get("account_reference_list", [])
    updated_proj_accounts = []
    for _acc in project_accounts:
        _acc_uuid = _acc["uuid"]
        account_cache_data = Cache.get_entity_data_using_uuid(
            entity_type="account", uuid=_acc_uuid
        )
        if not account_cache_data:
            LOG.error(
                "Account (uuid={}) not found. Please update cache".format(_acc_uuid)
            )
            sys.exit("Account (uuid={}) not found".format(_acc_uuid))

        if account_cache_data["name"] not in remove_account_list:
            updated_proj_accounts.append(_acc)
        else:
            project_usage_payload["filter"]["account_reference_list"].append(_acc_uuid)

    project_account_uuids = [_e["uuid"] for _e in updated_proj_accounts]
    for _acc in add_account_list:
        account_cache_data = Cache.get_entity_data(entity_type="account", name=_acc)
        if not account_cache_data:
            LOG.error("Account (name={}) not found. Please update cache".format(_acc))
            sys.exit("Account (name={}) not found".format(_acc))

        # Account already present
        if account_cache_data["uuid"] in project_account_uuids:
            continue

        updated_proj_accounts.append(
            {"kind": "account", "name": _acc, "uuid": account_cache_data["uuid"]}
        )

    project_resources["account_reference_list"] = updated_proj_accounts

    LOG.info("Checking project usage")
    res, err = client.project.usage(project_uuid, project_usage_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    project_usage = res.json()
    msg_list = []
    should_update_project = is_project_updation_allowed(project_usage, msg_list)
    if not should_update_project:
        LOG.error("Project updation failed")
        click.echo("\n".join(msg_list))
        click.echo(
            json.dumps(
                project_usage["status"].get("resources", {}),
                indent=4,
                separators=(",", ": "),
            )
        )
        sys.exit(-1)

    quota_entities = {"project": project_uuid}

    if enable_quotas:
        res, err = _set_quota_state(
            client=client, state=QUOTA.STATE.ENABLED, quota_entities=quota_entities
        )

        if err:
            LOG.exception("Failed to enable quotas with error {}".format(err))
            sys.exit(-1)

    if disable_quotas:
        res, err = _set_quota_state(
            client=client, state=QUOTA.STATE.DISABLED, quota_entities=quota_entities
        )

        if err:
            LOG.exception("Failed to disable quotas with error {}".format(err))
            sys.exit(-1)

    LOG.info("Updating project '{}'".format(project_name))
    res, err = client.project.update(project_uuid, project_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    if LV(calm_version) >= LV("3.5.2") and LV(calm_version) < LV("3.6.1"):
        name = res["spec"]["project_detail"]["name"]
    else:
        name = res["spec"]["name"]
    stdout_dict = {
        "name": name,
        "uuid": res["metadata"]["uuid"],
        "execution_context": res["status"]["execution_context"],
    }

    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    # Remove project removed user and groups from acps
    LOG.info("Polling on project updation task")
    task_state = watch_project_task(
        project_uuid, res["status"]["execution_context"]["task_uuid"], poll_interval=4
    )
    if task_state not in PROJECT_TASK.FAILURE_STATES:
        if acp_remove_user_list or acp_remove_group_list:
            LOG.info("Updating project acps")
            remove_users_from_project_acps(
                project_uuid=project_uuid,
                remove_user_list=acp_remove_user_list,
                remove_group_list=acp_remove_group_list,
            )
    else:
        LOG.exception("Project updation task went to {} state".format(task_state))
        sys.exit(-1)

    LOG.info("Updating projects cache ...")
    Cache.update_one(entity_type=CACHE.ENTITY.PROJECT, uuid=project_uuid)
    LOG.info("[Done]")


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
    watch_project_task(
        project_uuid, res["status"]["execution_context"]["task_uuid"], poll_interval=4
    )


def is_project_updation_allowed(project_usage, msg_list):
    """
    Returns whether project update is allowed.
    Will also update project_usage dict to contain only associate entities
    Args:
        project_usage (dict): project usage details
    Returns:
        _eusage (bool): is updation allowed
    """

    def is_entity_used(e_usage):

        entity_used = False
        app_cnt = e_usage.pop("app", 0)
        if app_cnt:
            entity_used = True
            e_usage["app"] = app_cnt

        brownfield_cnt = e_usage.get("blueprint", {}).pop("brownfield", 0)
        greenfield_cnt = e_usage.get("blueprint", {}).pop("greenfield", 0)
        if brownfield_cnt or greenfield_cnt:
            entity_used = True
            if brownfield_cnt:
                e_usage["blueprint"]["brownfield"] = brownfield_cnt
            if greenfield_cnt:
                e_usage["blueprint"]["greenfield"] = greenfield_cnt
        else:
            e_usage.pop("blueprint", None)

        endpoint_cnt = e_usage.pop("endpoint", 0)
        if endpoint_cnt:
            entity_used = True
            e_usage["endpoint"] = endpoint_cnt

        environment_cnt = e_usage.pop("environment", 0)
        if environment_cnt:
            entity_used = True
            e_usage["environment"] = environment_cnt

        runbook_cnt = e_usage.pop("runbook", 0)
        if runbook_cnt:
            entity_used = True
            e_usage["runbook"] = runbook_cnt

        return entity_used

    updation_allowed = True
    accounts_usage = project_usage["status"]["resources"].get("account_list", [])
    for _ac in accounts_usage:
        entity_used = is_entity_used(_ac["usage"])
        if entity_used:
            updation_allowed = False
            account_cache_data = Cache.get_entity_data_using_uuid(
                entity_type="account", uuid=_ac["uuid"]
            )
            msg_list.append(
                "Please disassociate the account '{}' (uuid='{}') references from existing entities".format(
                    account_cache_data["name"], account_cache_data["uuid"]
                )
            )

    subnets_usage = project_usage["status"]["resources"].get("subnet_list", [])
    for _snt in subnets_usage:
        entity_used = is_entity_used(_snt["usage"])
        if entity_used:
            updation_allowed = False
            subnet_cache_data = Cache.get_entity_data_using_uuid(
                entity_type=CACHE.ENTITY.AHV_SUBNET, uuid=_snt["uuid"]
            )
            msg_list.append(
                "Please disassociate the subnet '{}' (uuid='{}') references from existing entities".format(
                    subnet_cache_data["name"], subnet_cache_data["uuid"]
                )
            )

    cluster_usage = project_usage["status"]["resources"].get("cluster_list", [])
    for _snt in cluster_usage:
        entity_used = is_entity_used(_snt["usage"])
        if entity_used:
            updation_allowed = False
            cluster_cache_data = Cache.get_entity_data_using_uuid(
                entity_type=CACHE.ENTITY.AHV_CLUSTER, uuid=_snt["uuid"]
            )
            msg_list.append(
                "Please disassociate the cluster '{}' (uuid='{}') references from existing entities".format(
                    cluster_cache_data["name"], cluster_cache_data["uuid"]
                )
            )

    vpc_usage = project_usage["status"]["resources"].get("vpc_list", [])
    for _snt in vpc_usage:
        entity_used = is_entity_used(_snt["usage"])
        if entity_used:
            updation_allowed = False
            vpc_cache_data = Cache.get_entity_data_using_uuid(
                entity_type=CACHE.ENTITY.AHV_VPC, uuid=_snt["uuid"]
            )
            msg_list.append(
                "Please disassociate the vpc '{}' (uuid='{}') references from existing entities".format(
                    vpc_cache_data["name"], vpc_cache_data["uuid"]
                )
            )

    return updation_allowed


def update_payload_from_old_project_data(project_payload, old_project_payload):
    """
    updates the project_payload dict by appending the entities
    Args:
        project_payload (dict): updated project payload
        old_project_payload (dict): original payload before updating
    """

    updated_project_user_list = []
    for _user in project_payload["spec"]["resources"].get("user_reference_list", []):
        updated_project_user_list.append(_user["uuid"])

    updated_project_groups_list = []
    for _group in project_payload["spec"]["resources"].get(
        "external_user_group_reference_list", []
    ):
        updated_project_groups_list.append(_group["uuid"])

    updated_project_subnet_reference_list = []
    for _subnet in project_payload["spec"]["resources"].get(
        "subnet_reference_list", []
    ):
        updated_project_subnet_reference_list.append(_subnet["uuid"])

    updated_project_external_network_list = []
    for _external_network in project_payload["spec"]["resources"].get(
        "external_network_list", []
    ):
        updated_project_external_network_list.append(_external_network["uuid"])

    updated_project_account_reference_list = []
    for _account_reference in project_payload["spec"]["resources"].get(
        "account_reference_list", []
    ):
        updated_project_account_reference_list.append(_account_reference["uuid"])

    updated_project_vpc_reference_list = []
    for _vpc_reference in project_payload["spec"]["resources"].get(
        "vpc_reference_list", []
    ):
        updated_project_vpc_reference_list.append(_vpc_reference["uuid"])

    updated_project_cluster_reference_list = []
    for _cluster_reference in project_payload["spec"]["resources"].get(
        "cluster_reference_list", []
    ):
        updated_project_cluster_reference_list.append(_cluster_reference["uuid"])

    for _user in old_project_payload["spec"]["resources"].get(
        "user_reference_list", []
    ):
        if _user["uuid"] not in updated_project_user_list:
            project_payload["spec"]["resources"]["user_reference_list"].append(_user)

    for _group in old_project_payload["spec"]["resources"].get(
        "external_user_group_reference_list", []
    ):
        if _group["uuid"] not in updated_project_groups_list:
            project_payload["spec"]["resources"][
                "external_user_group_reference_list"
            ].append(_group)

    for _subnet in old_project_payload["spec"]["resources"].get(
        "subnet_reference_list", []
    ):
        if _subnet["uuid"] not in updated_project_subnet_reference_list:
            project_payload["spec"]["resources"]["subnet_reference_list"].append(
                _subnet
            )

    for _external_network in old_project_payload["spec"]["resources"].get(
        "external_network_list", []
    ):
        if _external_network["uuid"] not in updated_project_external_network_list:
            project_payload["spec"]["resources"]["external_network_list"].append(
                _external_network
            )

    for _account_reference in old_project_payload["spec"]["resources"].get(
        "account_reference_list", []
    ):
        if _account_reference["uuid"] not in updated_project_account_reference_list:
            project_payload["spec"]["resources"]["account_reference_list"].append(
                _account_reference
            )

    for _vpc_reference in old_project_payload["spec"]["resources"].get(
        "vpc_reference_list", []
    ):
        if _vpc_reference["uuid"] not in updated_project_vpc_reference_list:
            project_payload["spec"]["resources"]["vpc_reference_list"].append(
                _vpc_reference
            )

    for _cluster_reference in old_project_payload["spec"]["resources"].get(
        "cluster_reference_list", []
    ):
        if _cluster_reference["uuid"] not in updated_project_cluster_reference_list:
            project_payload["spec"]["resources"]["cluster_reference_list"].append(
                _cluster_reference
            )


def get_project_usage_payload(project_payload, old_project_payload):
    """
    Returns project_usage_payload (dict) which is used to check if project updation is allowed
    Args:
        project_payload (dict): updated project payload
        old_project_payload (dict): original payload before updating
    Returns:
        project_usage_payload (dict): payload for checking project usage
    """

    # Get the diff in subnet and account payload for project usage
    existing_subnets = [
        _subnet["uuid"]
        for _subnet in old_project_payload["spec"]["resources"].get(
            "subnet_reference_list", []
        )
    ]
    existing_subnets.extend(
        [
            _subnet["uuid"]
            for _subnet in old_project_payload["spec"]["resources"].get(
                "external_network_list", []
            )
        ]
    )

    new_subnets = [
        _subnet["uuid"]
        for _subnet in project_payload["spec"]["resources"].get(
            "subnet_reference_list", []
        )
    ]
    new_subnets.extend(
        [
            _subnet["uuid"]
            for _subnet in project_payload["spec"]["resources"].get(
                "external_network_list", []
            )
        ]
    )

    existing_accounts = [
        _acc["uuid"]
        for _acc in old_project_payload["spec"]["resources"].get(
            "account_reference_list", []
        )
    ]
    new_accounts = [
        _acc["uuid"]
        for _acc in project_payload["spec"]["resources"].get(
            "account_reference_list", []
        )
    ]

    existing_vpcs = [
        _vpc["uuid"]
        for _vpc in old_project_payload["spec"]["resources"].get(
            "vpc_reference_list", []
        )
    ]

    new_vpcs = [
        _vpc["uuid"]
        for _vpc in project_payload["spec"]["resources"].get("vpc_reference_list", [])
    ]

    existing_clusters = [
        _cluster["uuid"]
        for _cluster in old_project_payload["spec"]["resources"].get(
            "cluster_reference_list", []
        )
    ]

    new_clusters = [
        _cluster["uuid"]
        for _cluster in project_payload["spec"]["resources"].get(
            "cluster_reference_list", []
        )
    ]

    project_usage_payload = {
        "filter": {
            "subnet_reference_list": list(set(existing_subnets) - set(new_subnets)),
            "account_reference_list": list(set(existing_accounts) - set(new_accounts)),
            "vpc_reference_list": list(set(existing_vpcs) - set(new_vpcs)),
            "cluster_reference_list": list(set(existing_clusters) - set(new_clusters)),
        }
    }

    return project_usage_payload
