from .entity import EntityType, Entity
from .validator import PropertyValidator


# Blueprint

class BlueprintType(EntityType):
    __schema_name__ = "Blueprint"


class BlueprintValidator(PropertyValidator, openapi_type="blueprint"):
    __default__ = None
    __kind__ = BlueprintType


def blueprint(**kwargs):
    name = getattr(BlueprintType, "__schema_name__")
    bases = (Entity, )
    return BlueprintType(name, bases, kwargs)


Blueprint = blueprint()
