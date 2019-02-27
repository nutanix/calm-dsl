from .entity import EntityType, Entity
from .validator import PropertyValidator


# Port

class PortType(EntityType):
    __schema_name__ = "Port"


class PortValidator(PropertyValidator, openapi_type="port"):
    __default__ = None
    __kind__ = PortType


class Port(Entity, metaclass=PortType):
    pass


def port(**kwargs):
    name = getattr(PortType, "__schema_name__")
    bases = (Entity, )
    return PortType(name, bases, kwargs)


def port_type(cls):
    name = cls.__name__
    bases = (Entity, )
    kwargs = dict(cls.__dict__) # class dict is mappingproxy
    return PortType(name, bases, kwargs)
