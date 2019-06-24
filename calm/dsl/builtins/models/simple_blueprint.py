from .entity import EntityType, Entity
from .validator import PropertyValidator

from .blueprint import blueprint


# Simple Blueprint


class SimpleBlueprintType(EntityType):
    __schema_name__ = "SimpleBlueprint"
    __openapi_type__ = "app_simple_blueprint"

    def create_blueprint(cls):
        """Returns blueprint given a simple blueprint"""

        """
        UserBlueprint = blueprint()
        UserBlueprint.credentials = cls.credentials
        """

        return cls.__dict__


class SimpleBlueprintValidator(PropertyValidator, openapi_type="app_simple_blueprint"):
    __default__ = None
    __kind__ = SimpleBlueprintType


def simple_blueprint(**kwargs):
    name = getattr(SimpleBlueprintType, "__schema_name__")
    bases = (Entity,)
    return SimpleBlueprintType(name, bases, kwargs)


SimpleBlueprint = simple_blueprint()
