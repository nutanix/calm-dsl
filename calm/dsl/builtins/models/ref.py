from .entity import EntityType, Entity
from .validator import PropertyValidator


# Ref

class RefType(EntityType):
    __schema_name__ = "Ref"


class Ref(Entity, metaclass=RefType):
    pass


def ref(cls):

    kwargs = {}
    kwargs["name"] = str(cls)
    kwargs["kind"] = getattr(cls, "__kind__", None)
    return RefType("", (Entity, ), kwargs)


class RefValidator(PropertyValidator, openapi_type="ref"):

    __default__ = None
    __kind__ = RefType
