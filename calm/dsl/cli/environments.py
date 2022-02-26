import sys
import uuid
import click
import json
import time
import arrow
from prettytable import PrettyTable
from ruamel import yaml

from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.builtins import create_environment_payload, Environment
from calm.dsl.builtins.models.helper.common import get_project
from calm.dsl.tools import get_module_from_file
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle

from .utils import (
    get_name_query,
    highlight_text,
)

LOG = get_logging_handle(__name__)


def create_environment(env_payload):

    client = get_api_client()

    env_payload.pop("status", None)

    env_name = env_payload["spec"]["name"]
    LOG.info("Creating environment '{}'".format(env_name))
    res, err = client.environment.create(env_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    env_uuid = res["metadata"]["uuid"]
    env_state = res["status"]["state"]
    LOG.info(
        "Environment '{}' created successfully. Environment state: '{}'".format(
            env_name, env_state
        )
    )

    stdout_dict = {"name": env_name, "uuid": env_uuid}

    return stdout_dict


def compile_environment_dsl_class(env_cls, metadata=dict()):
    """
    Helper to compile the environment class
    Args:
        env_cls (Environment object): class for environment
        metadata (dict): Metadata object
    Returns:
        response (object): Response object containing environment object details
    """

    infra = getattr(env_cls, "providers", [])
    if not infra:
        LOG.warning(
            "From Calm v3.2, providers(infra) will be required to use environment for blueprints/marketplace usage"
        )

    UserEnvPayload, _ = create_environment_payload(env_cls, metadata=metadata)
    env_payload = UserEnvPayload.get_dict()

    # Pop default attribute from credentials
    for cred in env_payload["spec"]["resources"].get("credential_definition_list", []):
        cred.pop("default", None)

    # Adding uuid to creds and substrates
    for cred in env_payload["spec"]["resources"].get("credential_definition_list", []):
        cred["uuid"] = str(uuid.uuid4())

    for sub in env_payload["spec"]["resources"].get("substrate_definition_list", []):
        sub["uuid"] = str(uuid.uuid4())

    # Adding uuid readiness-probe
    cred_name_uuid_map = {}
    for cred in env_payload["spec"]["resources"].get("credential_definition_list", []):
        cred_name_uuid_map[cred["name"]] = cred["uuid"]

    for sub in env_payload["spec"]["resources"].get("substrate_definition_list", []):
        try:
            cred_ref_obj = sub["readiness_probe"]["login_credential_local_reference"]
            cred_ref_obj["uuid"] = cred_name_uuid_map[cred_ref_obj["name"]]
        except Exception:
            pass

    # TODO check if credential ref is working in attributes consuming credentials

    return env_payload


def compile_environment_command(env_file, project_name, out):
    """
    Compiles a DSL (Python) environment into JSON or YAML
    Args:
        env_file (str): Location for environment python file
        project_name (str): Project name
        out (str): Output format
    Returns:
        stdout (object): environment payload
    """

    # Update project on context
    ContextObj = get_context()
    ContextObj.update_project_context(project_name=project_name)

    user_env_module = get_environment_module_from_file(env_file)
    UserEnvironment = get_env_class_from_module(user_env_module)
    if UserEnvironment is None:
        LOG.error("User environment not found in {}".format(env_file))
        return

    env_payload = compile_environment_dsl_class(UserEnvironment)

    # Reset context
    ContextObj.reset_configuration()

    if out == "json":
        click.echo(json.dumps(env_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(env_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def create_environment_from_dsl_class(env_cls, env_name="", metadata=dict()):
    """
    Helper creates an environment from dsl environment class
    Args:
        env_cls (Environment object): class for environment
        env_name (str): Environment name (Optional)
        metadata (dict): Metadata object
    Returns:
        response (object): Response object containing environment object details
    """

    env_payload = compile_environment_dsl_class(env_cls, metadata)

    if env_name:
        env_payload["spec"]["name"] = env_name
        env_payload["metadata"]["name"] = env_name

    return create_environment(env_payload)


def update_project_envs(project_name, remove_env_uuids=[], add_env_uuids=[]):
    """
    Update project with the environment reference list if not present
    Args:
        project_name(str): Name of project
        remove_env_uuids(list): list of env uuids to be removed from project
        add_env_uuids(list): list of env uuid to be added in project
    Returns: None
    """
    if not (remove_env_uuids or add_env_uuids):
        return

    project_payload = get_project(project_name)
    project_payload.pop("status", None)

    env_list = project_payload["spec"]["resources"].get(
        "environment_reference_list", []
    )
    for _eu in add_env_uuids:
        env_list.append({"kind": "environment", "uuid": _eu})

    final_env_list = []
    for _edata in env_list:
        if _edata["uuid"] not in remove_env_uuids:
            final_env_list.append(_edata)

    project_payload["spec"]["resources"]["environment_reference_list"] = final_env_list
    project_uuid = project_payload["metadata"]["uuid"]

    # TODO remove this infunction imports
    from .projects import update_project

    return update_project(project_uuid, project_payload)


def get_environment_module_from_file(env_file):
    """Returns Environment module given a user environment dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_environment", env_file)


def get_env_class_from_module(user_env_module):
    """Returns environment class given a module"""

    UserEnvironment = None
    for item in dir(user_env_module):
        obj = getattr(user_env_module, item)
        if isinstance(obj, type(Environment)):
            if obj.__bases__[0] == Environment:
                UserEnvironment = obj

    return UserEnvironment


def create_environment_from_dsl_file(
    env_file, env_name, project_name, no_cache_update=False
):
    """
    Helper creates an environment from dsl file (for calm_version >= 3.2)
    Args:
        env_file (str): Location for environment python file
        env_name (str): Environment name
        project_name (str): Project name
    Returns:
        response (object): Response object containing environment object details
    """

    # Update project on context
    ContextObj = get_context()
    ContextObj.update_project_context(project_name=project_name)

    user_env_module = get_environment_module_from_file(env_file)
    UserEnvironment = get_env_class_from_module(user_env_module)
    if UserEnvironment is None:
        LOG.error("User environment not found in {}".format(env_file))
        return

    env_std_out = create_environment_from_dsl_class(
        env_cls=UserEnvironment, env_name=env_name
    )

    # Reset context
    ContextObj.reset_configuration()

    LOG.info("Updating project for environment configuration")
    update_project_envs(project_name, add_env_uuids=[env_std_out.get("uuid")])
    LOG.info("Project updated successfully")

    click.echo(json.dumps(env_std_out, indent=4, separators=(",", ": ")))

    if no_cache_update:
        LOG.info("skipping environments cache update")
    else:
        LOG.info("Updating environments cache ...")
        Cache.add_one(
            entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=env_std_out.get("uuid")
        )
        LOG.info("[Done]")


def update_environment_from_dsl_file(
    env_name, env_file, project_name, no_cache_update=False
):
    """
    Helper updates   an environment from dsl file (for calm_version >= 3.2)
    Args:
        env_name (str): Environment name
        env_file (str): Location for environment python file
        project_name (str): Project name
    Returns:
        response (object): Response object containing environment object details
    """

    # Update project on context
    ContextObj = get_context()
    ContextObj.update_project_context(project_name=project_name)

    environment = get_environment(env_name, project_name)
    environment_id = environment["metadata"]["uuid"]

    env_data_to_upload = get_environment_by_uuid(environment_id)
    env_data_to_upload.pop("status", None)

    # TODO Merge these module-file logic to single helper
    user_env_module = get_environment_module_from_file(env_file)
    UserEnvironment = get_env_class_from_module(user_env_module)
    if UserEnvironment is None:
        LOG.error("User environment not found in {}".format(env_file))
        sys.exit("User environment not found in {}".format(env_file))

    env_new_payload = compile_environment_dsl_class(UserEnvironment)

    # Overriding exsiting substrates and credentials (new-ones)
    env_data_to_upload["spec"]["resources"][
        "substrate_definition_list"
    ] = env_new_payload["spec"]["resources"]["substrate_definition_list"]
    env_data_to_upload["spec"]["resources"][
        "credential_definition_list"
    ] = env_new_payload["spec"]["resources"]["credential_definition_list"]
    env_data_to_upload["spec"]["resources"]["infra_inclusion_list"] = env_new_payload[
        "spec"
    ]["resources"]["infra_inclusion_list"]

    # Reset context
    ContextObj.reset_configuration()

    # Update environment
    LOG.info("Updating environment '{}'".format(env_name))
    client = get_api_client()
    res, err = client.environment.update(
        uuid=environment_id, payload=env_data_to_upload
    )
    if err:
        LOG.error(err)
        sys.exit(err["error"])

    res = res.json()
    stdout_dict = {
        "name": res["metadata"]["name"],
        "uuid": res["metadata"]["uuid"],
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    if no_cache_update:
        LOG.info("skipping environments cache update")
    else:
        LOG.info("Updating environments cache ...")
        Cache.update_one(entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=environment_id)
        LOG.info("[Done]")


def get_project_environment(name=None, uuid=None, project_name=None, project_uuid=None):
    """Get project and environment with the given project and environment name or uuid. Raises exception if
    environment doesn't belong to the project"""

    client = get_api_client()
    project_data = get_project(project_name, project_uuid)
    project_uuid = project_data["metadata"]["uuid"]
    project_name = project_data["status"]["name"]
    environments = project_data["status"]["resources"]["environment_reference_list"]
    project_environments = {row["uuid"]: True for row in environments}

    if not name and not uuid:
        return None, project_data

    if uuid is None:
        params = {"filter": "name=={};project_reference=={}".format(name, project_uuid)}
        LOG.info(
            "Searching for the environment {} under project {}".format(
                name, project_name
            )
        )
        res, err = client.environment.list(params=params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities")
        if not entities:
            raise Exception(
                "No environment with name {} found in project {}".format(
                    name, project_name
                )
            )

        environment = entities[0]
        uuid = environment["metadata"]["uuid"]

    if not project_environments.get(uuid):
        raise Exception(
            "No environment with name {} found in project {}".format(name, project_name)
        )

    LOG.info("Environment {} found ".format(name))

    # for getting additional fields
    return get_environment_by_uuid(uuid), project_data


def get_environment_by_uuid(environment_uuid):
    """Fetch the environment with the given name under the given project"""
    LOG.info("Fetching details of environment (uuid='{}')".format(environment_uuid))
    client = get_api_client()
    res, err = client.environment.read(environment_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    environment = res.json()
    return environment


def get_environment_list(name, filter_by, limit, offset, quiet, out, project_name):
    """Get the environment, optionally filtered by a string"""

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if project_name:
        project_data = get_project(project_name)
        project_id = project_data["metadata"]["uuid"]
        filter_query = filter_query + ";project_reference=={}".format(project_id)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.environment.list(params=params)

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch environments from {}".format(pc_ip))
        return

    if out == "json":
        click.echo(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No environment found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "PROJECT",
        "STATE",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        project = (
            metadata["project_reference"]["name"]
            if "project_reference" in metadata
            else None
        )

        creation_time = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(project),
                highlight_text(row["state"]),
                highlight_text(time.ctime(creation_time)),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(row.get("uuid", "")),
            ]
        )
    click.echo(table)


def get_environment(environment_name, project_name):
    """returns the environment payload"""

    client = get_api_client()
    payload = {
        "length": 250,
        "offset": 0,
        "filter": "name=={}".format(environment_name),
    }

    if project_name:
        project = get_project(project_name)
        project_id = project["metadata"]["uuid"]
        payload["filter"] += ";project_reference=={}".format(project_id)

    res, err = client.environment.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if res["metadata"]["total_matches"] == 0:
        LOG.error("Environment '{}' not found".format(environment_name))
        sys.exit(-1)

    return res["entities"][0]


def delete_environment(environment_name, project_name, no_cache_update=False):

    client = get_api_client()
    environment = get_environment(environment_name, project_name)
    environment_id = environment["metadata"]["uuid"]
    _, err = client.environment.delete(environment_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))
    LOG.info("Environment {} deleted".format(environment_name))

    LOG.info("Updating project for environment configuration")
    update_project_envs(project_name, remove_env_uuids=[environment_id])

    if no_cache_update:
        LOG.info("skipping environments cache update")
    else:
        LOG.info("Updating environments cache ...")
        Cache.delete_one(entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=environment_id)
        LOG.info("[Done]")
