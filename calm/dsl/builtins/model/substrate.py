from .base import EntityType, Entity
from .base import PropertyValidator
from .base import SCHEMAS


## Substrate

class SubstrateType(EntityType):
    __schema__ = SCHEMAS["Substrate"]


class Substrate(Entity, metaclass=SubstrateType):
    pass


class SubstrateValidator(PropertyValidator, openapi_type="substrate"):

    __default__ = None
    __kind__ = SubstrateType


class SubstrateListValidator(SubstrateValidator, openapi_type="substrates"):

    __default__ = []
