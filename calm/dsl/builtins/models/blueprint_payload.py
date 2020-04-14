from .entity import EntityType, Entity
from .validator import PropertyValidator
from .blueprint import BlueprintType
from .simple_blueprint import SimpleBlueprintType


# Blueprint Payload


class BlueprintPayloadType(EntityType):
    __schema_name__ = "BlueprintPayload"
    __openapi_type__ = "app_blueprint_payload"


class BlueprintPayloadValidator(
    PropertyValidator, openapi_type="app_blueprint_payload"
):
    __default__ = None
    __kind__ = BlueprintPayloadType


def _blueprint_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return BlueprintPayloadType(name, bases, kwargs)


BlueprintPayload = _blueprint_payload()


def create_blueprint_payload(UserBlueprint, categories=None):

    err = {"error": "", "code": -1}

    if UserBlueprint is None:
        err["error"] = "Given blueprint is empty."
        return None, err

    if not isinstance(UserBlueprint, (BlueprintType, SimpleBlueprintType)):
        err["error"] = "Given blueprint is not of type Blueprint"
        return None, err

    spec = {
        "name": UserBlueprint.__name__,
        "description": UserBlueprint.__doc__ or "",
        "resources": UserBlueprint,
    }

    metadata = {"spec_version": 1, "kind": "blueprint", "name": UserBlueprint.__name__}

    if categories:
        metadata["categories"] = categories

    UserBlueprintPayload = _blueprint_payload()
    UserBlueprintPayload.metadata = metadata
    UserBlueprintPayload.spec = spec

    return UserBlueprintPayload, None
