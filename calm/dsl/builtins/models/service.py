from .entity import EntityType, Entity
from .validator import PropertyValidator


# Service

class ServiceType(EntityType):
    __schema_name__ = "Service"


class Service(Entity, metaclass=ServiceType):
    pass


def service(**kwargs):
    return ServiceType("", (Entity, ), kwargs)


class ServiceValidator(PropertyValidator, openapi_type="service"):

    __default__ = None
    __kind__ = ServiceType
