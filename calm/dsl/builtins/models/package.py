from .entity import EntityType, Entity
from .validator import PropertyValidator


# Package

class PackageType(EntityType):
    __schema_name__ = "Package"


class PackageValidator(PropertyValidator, openapi_type="package"):
    __default__ = None
    __kind__ = PackageType


def package(**kwargs):
    name = getattr(PackageType, "__schema_name__")
    bases = (Entity, )
    return PackageType(name, bases, kwargs)


Package = package()
