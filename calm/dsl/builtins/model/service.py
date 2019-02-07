from .entity import EntityType, Entity
from .validator import PropertyValidator
from .base import SCHEMAS


## Service

class ServiceType(EntityType):
    __schema__ = SCHEMAS["Service"]


class Service(Entity, metaclass=ServiceType):
    pass


class ServiceValidator(PropertyValidator, openapi_type="service"):

    __default__ = None
    __kind__ = ServiceType


class ServiceListValidator(ServiceValidator, openapi_type="services"):

    __default__ = []
