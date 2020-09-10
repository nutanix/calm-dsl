from .entity import EntityType, Entity
from .validator import PropertyValidator
from .environment import EnvironmentType


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


def create_environment_payload(UserEnvironment):

    err = {"error": "", "code": -1}

    if UserEnvironment is None:
        err["error"] = "Given project is empty."
        return None, err

    if not isinstance(UserEnvironment, EnvironmentType):
        err["error"] = "Given environment is not of type Environment"
        return None, err

    spec = {
        "name": UserEnvironment.__name__,
        "description": UserEnvironment.__doc__ or "",
        "resources": UserEnvironment,
    }

    metadata = {
        "spec_version": 1,
        "kind": "environment",
        "name": UserEnvironment.__name__,
    }

    UserEnvironmentPayload = _environment_payload()
    UserEnvironmentPayload.metadata = metadata
    UserEnvironmentPayload.spec = spec

    return UserEnvironmentPayload, None
