from .entity import EntityType, Entity
from .validator import PropertyValidator


# Service

class ServiceType(EntityType):
    __schema_name__ = "Service"


class ServiceValidator(PropertyValidator, openapi_type="service"):
    __default__ = None
    __kind__ = ServiceType


def service(**kwargs):
    name = getattr(ServiceType, "__schema_name__")
    bases = (Entity, )
    return ServiceType(name, bases, kwargs)


Service = service()
