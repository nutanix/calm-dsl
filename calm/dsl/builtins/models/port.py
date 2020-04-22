from .entity import EntityType, Entity
from .validator import PropertyValidator


# Port


class PortType(EntityType):
    __schema_name__ = "Port"
    __openapi_type__ = "app_port"


class PortValidator(PropertyValidator, openapi_type="app_port"):
    __default__ = None
    __kind__ = PortType


def port(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PortType(name, bases, kwargs)


Port = port()
