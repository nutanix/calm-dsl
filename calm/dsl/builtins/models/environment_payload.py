import sys
import uuid
from distutils.version import LooseVersion as LV

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .environment import EnvironmentType
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache, Version
from calm.dsl.constants import CACHE

LOG = get_logging_handle(__name__)
# Blueprint Payload


class EnvironmentPayloadType(EntityType):
    __schema_name__ = "EnvironmentPayload"
    __openapi_type__ = "app_environment_payload"


class EnvironmentPayloadValidator(
    PropertyValidator, openapi_type="app_environment_payload"
):
    __default__ = None
    __kind__ = EnvironmentPayloadType


def _environment_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return EnvironmentPayloadType(name, bases, kwargs)


EnvironmentPayload = _environment_payload()


def create_environment_payload(UserEnvironment, metadata=dict()):
    """
    Creates environment payload
    Args:
        UserEnvironment(object): Environment object
        metadata (dict) : Metadata for environment
    Returns:
        response(tuple): tuple consisting of environment payload object and error
    """

    err = {"error": "", "code": -1}

    if UserEnvironment is None:
        err["error"] = "Given environment is empty."
        return None, err

    if not isinstance(UserEnvironment, EnvironmentType):
        err["error"] = "Given environment is not of type Environment"
        return None, err

    spec = {
        "name": UserEnvironment.__name__,
        "description": UserEnvironment.__doc__ or "",
        "resources": UserEnvironment,
    }

    env_project = metadata.get("project_reference", {}).get("name", "")
    if not env_project:
        ContextObj = get_context()
        project_config = ContextObj.get_project_config()
        env_project = project_config["name"]

    project_cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.PROJECT, name=env_project
    )
    if not project_cache_data:
        LOG.error("Project {} not found.".format(env_project))
        sys.exit("Project {} not found.".format(env_project))

    metadata_payload = {
        "spec_version": 1,
        "kind": "environment",
        "name": UserEnvironment.__name__,
        "uuid": str(uuid.uuid4()),
    }

    calm_version = Version.get_version("Calm")
    if LV(calm_version) >= LV("3.2.0"):
        metadata_payload["project_reference"] = {
            "kind": "project",
            "name": project_cache_data["name"],
            "uuid": project_cache_data["uuid"],
        }

    UserEnvironmentPayload = _environment_payload()
    UserEnvironmentPayload.metadata = metadata_payload
    UserEnvironmentPayload.spec = spec

    return UserEnvironmentPayload, None
