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
    name = getattr(RefType, "__schema_name__")
    bases = (Entity,)
    return RefType(name, bases, kwargs)


Ref = _ref()


def ref(cls):

    kwargs = {}
    kwargs["name"] = str(cls)
    kwargs["kind"] = getattr(cls, "__kind__")

    return _ref(**kwargs)
