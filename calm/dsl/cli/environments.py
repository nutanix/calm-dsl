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
