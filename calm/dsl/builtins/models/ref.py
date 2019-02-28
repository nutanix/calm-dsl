from .entity import EntityType, Entity
from .validator import PropertyValidator


# Ref

class RefType(EntityType):
    __schema_name__ = "Ref"


class RefValidator(PropertyValidator, openapi_type="ref"):
    __default__ = None
    __kind__ = RefType


def _ref(**kwargs):
    name = getattr(RefType, "__schema_name__")
    bases = (Entity, )
    return RefType(name, bases, kwargs)


def ref_type(cls):
    name = cls.__name__
    bases = (Entity, )
    kwargs = dict(cls.__dict__) # class dict is mappingproxy
    return RefType(name, bases, kwargs)


Ref = _ref()


def ref(cls):

    kwargs = {}
    kwargs["name"] = str(cls)
    kwargs["kind"] = getattr(cls, "__kind__", None)

    return _ref(**kwargs)
