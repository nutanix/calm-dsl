from .entity import EntityType, Entity
from .validator import PropertyValidator


# Ref

class RefType(EntityType):
    __schema_name__ = "Ref"


class Ref(Entity, metaclass=RefType):
    pass


def ref(**kwargs):
    return RefType("", (Entity, ), kwargs)


class RefValidator(PropertyValidator, openapi_type="ref"):

    __default__ = None
    __kind__ = RefType
