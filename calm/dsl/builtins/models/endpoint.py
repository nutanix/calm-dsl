from .entity import EntityType, Entity
from .validator import PropertyValidator
import uuid


# Endpoint

class EndpointType(EntityType):
    __schema_name__ = "Endpoint"
    __openapi_type__ = "app_endpoint"

    ALLOWED_FRAGMENT_ACTIONS = {
        "__pre_create__": "pre_action_create",
        "__post_delete__": "post_action_delete",
    }

    def compile(cls):
        cdict = super().compile()
        cdict["uuid"] = str(uuid.uuid4())
        return cdict

    def get_task_target(cls):
        return cls.get_ref()


class EndpointValidator(PropertyValidator, openapi_type="app_endpoint"):
    __default__ = None
    __kind__ = EndpointType


def endpoint(**kwargs):
    name = kwargs.get("name") or getattr(EndpointType, "__schema_name__")
    bases = (Entity,)
    return EndpointType(name, bases, kwargs)


Endpoint = endpoint()
