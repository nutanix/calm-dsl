from .entity import EntityType, Entity


# Blueprint

class BlueprintType(EntityType):
    __schema_name__ = "Blueprint"


class Blueprint(Entity, metaclass=BlueprintType):
    pass
