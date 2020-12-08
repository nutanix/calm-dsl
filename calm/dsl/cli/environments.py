import sys
import uuid

from calm.dsl.builtins import create_environment_payload
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def create_environment(env_payload):

    client = get_api_client()

    env_payload.pop("status", None)

    # Pop default attribute from credentials
    for cred in env_payload["spec"]["resources"].get("credential_definition_list", []):
        cred.pop("default", None)

    # Adding uuid to creds and substrates
    for cred in env_payload["spec"]["resources"].get("credential_definition_list", []):
        cred["uuid"] = str(uuid.uuid4())

    for sub in env_payload["spec"]["resources"].get("substrate_definition_list", []):
        sub["uuid"] = str(uuid.uuid4())

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


def create_environment_from_dsl_class(env_class):

    env_payload = None
    UserEnvPayload, _ = create_environment_payload(env_class)
    env_payload = UserEnvPayload.get_dict()

    return create_environment(env_payload)


def get_project(name="", project_uuid=""):
    """get project with given name or uuid"""
    if not (name or project_uuid):
        raise Exception("One of name or uuid must be provided")

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
        LOG.info("Searching for the environment {} under project {}".format(name, project_name))
        res, err = client.environment.list(params=params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities")
        if not entities:
            raise Exception("No environment with name {} found in project {}".format(name, project_name))

        environment = entities[0]
        uuid = environment["metadata"]["uuid"]

    if not project_environments.get(uuid):
        raise Exception("No environment with name {} found in project {}".format(name, project_name))

    LOG.info("Environment {} found ".format(name))

    # for getting additional fields
    return get_environment_by_uuid(uuid), project_data


def get_environment_by_uuid(environment_uuid):
    """ Fetch the environment with the given name under the given project """
    LOG.info("Fetching details of environment (uuid='{}')".format(environment_uuid))
    client = get_api_client()
    res, err = client.environment.read(environment_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    environment = res.json()
    return environment
