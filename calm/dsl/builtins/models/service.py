from .entity import EntityType, Entity
from .validator import PropertyValidator


# Service

class ServiceType(EntityType):
    __schema_name__ = "Service"


class ServiceValidator(PropertyValidator, openapi_type="service"):
    __default__ = None
    __kind__ = ServiceType


class Service(Entity, metaclass=ServiceType):
    pass


def service(**kwargs):
    name = getattr(ServiceType, "__schema_name__")
    bases = (Entity, )
    return ServiceType(name, bases, kwargs)


def service_type(cls):
    name = cls.__name__
    bases = (Entity, )
    kwargs = dict(cls.__dict__) # class dict is mappingproxy
    return ServiceType(name, bases, kwargs)
