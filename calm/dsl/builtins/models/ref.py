from .entity import EntityType, Entity
from .validator import PropertyValidator


# Ref


class RefType(EntityType):
    __schema_name__ = "Ref"
    __openapi_type__ = "app_ref"


class RefValidator(PropertyValidator, openapi_type="app_ref"):
    __default__ = None
    __kind__ = RefType


def _ref(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return RefType(name, bases, kwargs)


Ref = _ref()


def ref(cls):

    if isinstance(cls, RefType):
        return cls

    return cls.get_ref()
