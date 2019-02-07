from .base import EntityType, Entity
from .validator import PropertyValidator
from .base import SCHEMAS


## Port

class PortType(EntityType):
    __schema__ = SCHEMAS["Port"]


class Port(Entity, metaclass=PortType):
    pass


class PortValidator(PropertyValidator, openapi_type="port"):

    __default__ = None
    __kind__ = PortType


class PortListValidator(PortValidator, openapi_type="ports"):

    __default__ = []
