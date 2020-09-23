from calm.dsl.config import get_context

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .blueprint import BlueprintType
from .simple_blueprint import SimpleBlueprintType
from .ref import Ref


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


def create_blueprint_payload(UserBlueprint, metadata={}):

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

    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    project_config = ContextObj.get_project_config()
    config_categories = ContextObj.get_categories_config()

    # Set the blueprint name and kind correctly
    metadata["name"] = UserBlueprint.__name__
    metadata["kind"] = "blueprint"

    #  Project will be taken from config if not provided
    if not metadata.get("project_reference", {}):
        project_name = project_config["name"]
        metadata["project_reference"] = Ref.Project(project_name)

    #  User will be taken from config if not provided
    if not metadata.get("owner_reference", {}):
        user_name = server_config["pc_username"]
        metadata["owner_reference"] = Ref.User(user_name)

    #  Categories will be taken from config if not provided
    if not metadata.get("categories", {}):
        metadata["categories"] = config_categories

    metadata["kind"] = "blueprint"
    UserBlueprintPayload = _blueprint_payload()
    UserBlueprintPayload.metadata = metadata
    UserBlueprintPayload.spec = spec

    return UserBlueprintPayload, None
