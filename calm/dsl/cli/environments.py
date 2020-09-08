import sys
import uuid

from calm.dsl.tools import get_module_from_file
from calm.dsl.builtins import Environment, create_environment_payload
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_environment_module_from_file(project_file):
    """Returns Environment module given a user project dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_environment", project_file)


def get_environment_class_from_module(user_environment_module, env_name=None):
    """Returns environment class given a module"""

    UserEnvironment = None
    for item in dir(user_environment_module):
        obj = getattr(user_environment_module, item)
        if isinstance(obj, type(Environment)):
            if obj.__bases__[0] == Environment:
                if (
                    env_name and env_name != obj.__name__
                ):  # TODO Also check for name parameter
                    continue

                # If name not given or given name is matched with obj name
                UserEnvironment = obj

    return UserEnvironment


def compile_environment(project_file, env_name=None):

    user_environment_module = get_environment_module_from_file(project_file)
    UserEnvironment = get_environment_class_from_module(
        user_environment_module, env_name=env_name
    )
    if UserEnvironment is None:
        return None

    env_payload = None
    UserEnvPayload, _ = create_environment_payload(UserEnvironment)
    env_payload = UserEnvPayload.get_dict()

    return env_payload


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

    """# Adding unique names to environment
    env_payload["spec"]["name"] = "Env_{}".format(str(uuid.uuid4()))
    env_payload["metadata"]["name"] = "Env_{}".format(str(uuid.uuid4()))"""

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
        "Created environment (uuid='{}'). Environment state: '{}'".format(
            env_uuid, env_state
        )
    )

    return env_uuid


def create_environment_from_dsl(project_file, env_name=None):
    """creates environment, filtered by name if given"""

    env_payload = compile_environment(project_file, env_name=env_name)
    if env_payload is None:
        err_msg = "Environment not found in {}".format(project_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return create_environment(env_payload)
