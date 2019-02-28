from .entity import EntityType, Entity
from .validator import PropertyValidator


# Variable

class VariableType(EntityType):
    __schema_name__ = "Variable"


class VariableValidator(PropertyValidator, openapi_type="variable"):
    __default__ = None
    __kind__ = VariableType


class Variable(Entity, metaclass=VariableType):
    pass


def setvar(name, value, **kwargs):

    kwargs["name"] = name
    kwargs["value"] = value

    # name = name.title() + getattr(VariableType, "__schema_name__")
    return VariableType(name, (Entity, ), kwargs)


def var(value, **kwargs):
    name = "Variable"
    return setvar(name, value, **kwargs)
