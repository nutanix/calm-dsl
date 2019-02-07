from .base import EntityType, Entity
from .base import PropertyValidator
from .base import SCHEMAS


## Blueprint

class BlueprintType(EntityType):
    __schema__ = SCHEMAS["Blueprint"]


class Blueprint(Entity, metaclass=BlueprintType):
    pass
