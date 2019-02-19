from .entity import EntityType, Entity
from .validator import PropertyValidator


# Port

class PortType(EntityType):
    __schema_name__ = "Port"


class Port(Entity, metaclass=PortType):
    pass


def port(**kwargs):
    return PortType("", (Entity, ), kwargs)


class PortValidator(PropertyValidator, openapi_type="port"):

    __default__ = None
    __kind__ = PortType
