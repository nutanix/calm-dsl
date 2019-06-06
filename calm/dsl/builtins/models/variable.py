from .entity import EntityType, Entity
from .validator import PropertyValidator


# Variable


class VariableType(EntityType):
    __schema_name__ = "Variable"
    __openapi_type__ = "app_variable"

    def compile(cls):
        cdict = super().compile()
        if not cdict.get("options", {}):
            del cdict["options"]
        if not cdict.get("regex", {}):
            del cdict["regex"]
        if not cdict.get("editables", {}):
            del cdict["editables"]
        return cdict


class VariableValidator(PropertyValidator, openapi_type="app_variable"):
    __default__ = None
    __kind__ = VariableType


def _var(**kwargs):
    name = getattr(VariableType, "__schema_name__")
    bases = (Entity,)
    return VariableType(name, bases, kwargs)


Variable = _var()


def setvar(name, value, **kwargs):

    kwargs["name"] = name
    kwargs["value"] = value

    # name = name.title() + getattr(VariableType, "__schema_name__")
    return VariableType(name, (Variable,), kwargs)


def simple_variable(value, label=None, runtime=False):
    editables = {}
    name = getattr(VariableType, "__schema_name__")
    if runtime:
        editables = {
            "value": True
        }
    if label is None:
        label = ""
    return setvar(name, value, label=label, editables=editables)
