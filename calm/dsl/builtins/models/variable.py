from .entity import EntityType, Entity
from .validator import PropertyValidator


# Variable

VARIABLE_VALUE_TYPES = {
    "int": "INT",
    "date": "DATE",
    "time": "TIME",
    "dict": "DICT",
    "string": "STRING",
    "data_time": "DATE_TIME",
    "multiline_string": "MULTILINE_STRING",
}

VARIABLE_DATA_TYPES = {
    "base": "BASE",
    "list": "LIST",
    "single_select_list": "SINGLE_SELECT_LIST",
}


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
        editables = {"value": True}
    if label is None:
        label = ""
    return setvar(name, value, label=label, editables=editables)


def _get_runtime_editables(object_):
    editables = {}
    if not isinstance(object_, dict):
        return True
    for key, value in object_.items():
        if isinstance(value, dict):
            editables[key] = _get_runtime_editables(value)
        if isinstance(value, list):
            editables[key] = {
                index: _get_runtime_editables(element)
                for index, element in enumerate(value)
            }
        else:
            editables[key] = True
    return editables


def _advanced_variable(
    name,
    value,
    type_,
    label=None,
    task=None,
    value_type=None,
    data_type=None,
    regex=None,
    options=None,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    kwargs = {"name": name, "value": str(value), "type": type_}
    editables = {}
    if label is not None:
        kwargs["label"] = label
        if runtime:
            editables["label"] = True
    if task is not None:
        if not getattr(task, "__kind__") == "app_task":
            raise TypeError(
                "Expected a Task for variable "
                + (name or "")
                + ", got {}".format(type(task))
            )
        task_attrs = getattr(task, "attrs")
        if not task_attrs:
            raise ValueError("Task for variable " + (name or "") + ", is not valid.")
        task_type = getattr(task, "type")
        if task_type not in ["HTTP", "EXEC"]:
            raise ValueError(
                "Task type for variable "
                + (name or "")
                + ", is not valid, Expected one of"
                + " ['HTTP', 'EXEC'], got {}".format(task_type)
            )
        kwargs["options"]["type"] = task_type
        kwargs["options"]["attrs"] = task_attrs
        if runtime:
            editables["attrs"] = _get_runtime_editables(task_attrs)
    if value_type is not None:
        value_type = value_type.upper()
        if value_type not in VARIABLE_VALUE_TYPES.values():
            raise ValueError("Invalid value_type provided for variable " + (name or ""))
        kwargs["value_type"] = value_type
        if runtime:
            editables["value_type"] = True
    if data_type is not None:
        data_type = data_type.upper()
        if data_type not in VARIABLE_DATA_TYPES.values():
            raise ValueError("Invalid data_type provided for variable " + (name or ""))
        kwargs["data_type"] = data_type
        if runtime:
            editables["data_type"] = True
    if regex is not None:
        if not getattr(task, "__kind__") == "app_task":
            raise TypeError(
                "Expected string in field regex for variable "
                + (name or "")
                + ", got {}".format(type(regex))
            )
        regex = {"value": regex, "should_validate": True}
        kwargs["regex"] = regex
        if runtime:
            editables["regex"] = _get_runtime_editables(regex)
    if options is not None:
        if kwargs.get("options", None) is not None:
            raise ValueError(
                "Variable options for variable "
                + (name or "")
                + "cannot be specified since it is being "
                + "fetched from a {} task".format(kwargs["options"]["type"])
            )
        if not isinstance(options, list):
            raise TypeError(
                "Expected list of options for variable "
                + (name or "")
                + ", got {}".format(type(options))
            )
        choices = []
        for choice in choices:
            if not isinstance(choice, str):
                raise TypeError(
                    "Expected list of string choices for options for variable "
                    + (name or "")
                    + ", got {}".format(type(choice))
                )
        options = {
            "type": "PREDEFINED",
            "choices": choices
        }
        kwargs["options"] = options
        if runtime:
            editables["options"] = _get_runtime_editables(options)
    if is_hidden is not None:
        kwargs["is_hidden"] = bool(is_hidden)
        if runtime:
            editables["is_hidden"] = True
    if is_mandatory is not None:
        kwargs["is_mandatory"] = bool(is_mandatory)
        if runtime:
            editables["is_mandatory"] = True

    return setvar(name, value, **kwargs)
