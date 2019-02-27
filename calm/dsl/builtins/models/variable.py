from .entity import EntityType, Entity
from .validator import PropertyValidator


# Variable

class VariableType(EntityType):
    __schema_name__ = "Variable"


class Variable(Entity, metaclass=VariableType):
    pass


def setvar(name, value, type="LOCAL", val_type="STRING", label=""):

    kwargs = {}
    kwargs["name"] = name
    kwargs["value"] = value
    kwargs["type"] = type
    kwargs["val_type"] = val_type
    kwargs["label"] = label

    return VariableType("", (Entity, ), kwargs)


class VariableValidator(PropertyValidator, openapi_type="variable"):

    __default__ = None
    __kind__ = VariableType
