from .entity import EntityType, Entity
from .validator import PropertyValidator


# Endpoint

class EndpointType(EntityType):
    __schema_name__ = "Endpoint"
    __openapi_type__ = "app_endpoint"

    def get_ref(cls, name=None):
        return super().get_ref(cls_name=name)

    def __call__(*args, **kwargs):
        pass


class EndpointValidator(PropertyValidator, openapi_type="app_endpoint"):
    __default__ = None
    __kind__ = EndpointType


def endpoint(**kwargs):
    name = kwargs.get("name") or getattr(EndpointType, "__schema_name__")
    bases = (Entity,)
    return EndpointType(name, bases, kwargs)


Endpoint = endpoint()
