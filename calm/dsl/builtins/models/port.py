from .entity import EntityType, Entity
from .validator import PropertyValidator


# Port

class PortType(EntityType):
    __schema_name__ = "Port"


class PortValidator(PropertyValidator, openapi_type="port"):
    __default__ = None
    __kind__ = PortType


def port(**kwargs):
    name = getattr(PortType, "__schema_name__")
    bases = (Entity, )
    return PortType(name, bases, kwargs)


Port = port()
