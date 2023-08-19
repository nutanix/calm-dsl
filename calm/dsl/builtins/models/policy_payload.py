from calm.dsl.config import get_context
from .entity import EntityType, Entity
from .policy import PolicyType
from .validator import PropertyValidator
from .calm_ref import Ref

# Policy
class PolicyPayloadType(EntityType):
    __schema_name__ = "PolicyPayload"
    __openapi_type__ = "policy_payload"


class PolicyPayloadValidator(PropertyValidator, openapi_type="policy_payload"):
    __default__ = None
    __kind__ = PolicyPayloadType


def _policy_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PolicyPayloadType(name, bases, kwargs)


def create_policy_payload(UserPolicy, metadata={}):

    err = {"error": "", "code": -1}

    if UserPolicy is None:
        err["error"] = "Given policy is empty."
        return None, err

    if not isinstance(UserPolicy, PolicyType):
        err["error"] = "Given policy is not of type Policy"
        return None, err

    spec = {
        "name": UserPolicy.__name__,
        "description": UserPolicy.__doc__ or "",
        "resources": UserPolicy,
    }

    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    project_config = ContextObj.get_project_config()
    config_categories = ContextObj.get_categories_config()

    # Set the policy name and kind correctly
    metadata["name"] = UserPolicy.__name__
    metadata["kind"] = "policy"

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

    # Add project-reference in category-list also for policy-scope
    if metadata.get("project_reference", {}):
        if not UserPolicy.category_list:
            UserPolicy.category_list = {}
        UserPolicy.category_list["Project"] = metadata["project_reference"]["name"]

    metadata["kind"] = "policy"
    UserPolicyPayload = _policy_payload()
    UserPolicyPayload.metadata = metadata
    UserPolicyPayload.spec = spec

    return UserPolicyPayload, None


PolicyPayload = _policy_payload()
