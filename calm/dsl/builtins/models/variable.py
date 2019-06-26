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


def setvar(name, value, type_="LOCAL", **kwargs):

    if name is None:
        name = getattr(VariableType, "__schema_name__")
    kwargs["name"] = name
    if value is not None:
        kwargs["value"] = value
    kwargs["type"] = type_

    return VariableType(name, (Variable,), kwargs)


def simple_variable(
    value,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    kwargs = {"is_hidden": is_hidden, "is_mandatory": is_mandatory}
    editables = {}
    name = getattr(VariableType, "__schema_name__")
    if runtime:
        editables = {"value": True}
        kwargs["editables"] = editables
    if label is not None:
        kwargs["label"] = label
    if regex is not None:
        if not isinstance(regex, str):
            raise TypeError(
                "Expected string in field regex for variable "
                + (name or "")
                + ", got {}".format(type(regex))
            )
        regex = {"value": regex, "should_validate": validate_regex}
        kwargs["regex"] = regex
    return setvar(name, value, **kwargs)


def simple_variable_secret(
    value,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    kwargs = {"is_hidden": is_hidden, "is_mandatory": is_mandatory}
    editables = {}
    name = getattr(VariableType, "__schema_name__")
    if runtime:
        editables = {"value": True}
        kwargs["editables"] = editables
    if label is not None:
        kwargs["label"] = label
    if regex is not None:
        if not isinstance(regex, str):
            raise TypeError(
                "Expected string in field regex for variable "
                + (name or "")
                + ", got {}".format(type(regex))
            )
        regex = {"value": regex, "should_validate": validate_regex}
        kwargs["regex"] = regex
    return setvar(name, value, type_="SECRET", **kwargs)


def _advanced_variable(
    type_,
    name=None,
    value=None,
    label=None,
    task=None,
    value_type=None,
    data_type=None,
    regex=None,
    validate_regex=False,
    options=None,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    kwargs = {"name": name, "value": value, "type": type_}
    if runtime:
        kwargs["editables"] = {"value": True}
    if label is not None:
        kwargs["label"] = label
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
    if value_type is not None:
        value_type = value_type.upper()
        if value_type not in VARIABLE_VALUE_TYPES.values():
            raise ValueError("Invalid value_type provided for variable " + (name or ""))
        kwargs["value_type"] = value_type
    if data_type is not None:
        data_type = data_type.upper()
        if data_type not in VARIABLE_DATA_TYPES.values():
            raise ValueError("Invalid data_type provided for variable " + (name or ""))
        kwargs["data_type"] = data_type
    if task is not None:
        if not getattr(task, "__kind__") == "app_task":
            raise TypeError(
                "Expected string in field regex for variable "
                + (name or "")
                + ", got {}".format(type(regex))
            )
        regex = {"value": regex, "should_validate": validate_regex}
        kwargs["regex"] = regex
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
        for choice in options:
            if not isinstance(choice, str):
                raise TypeError(
                    "Expected list of string choices for options for variable "
                    + (name or "")
                    + ", got {}".format(type(choice))
                )
            choices.append(choice)
        if value is None and len(choices) > 0:
            value = choices[0]
        if value not in choices:
            raise TypeError(
                "Default value for variable with options "
                + (name or "")
                + "is {}, which is not one of the options".format(value)
            )
        options = {"type": "PREDEFINED", "choices": choices}
        kwargs["options"] = options
    if is_hidden is not None:
        kwargs["is_hidden"] = bool(is_hidden)
    if is_mandatory is not None:
        kwargs["is_mandatory"] = bool(is_mandatory)

    return setvar(**kwargs)


def simple_variable_int(
    value,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        value=value,
        label=label,
        value_type="INT",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_date(
    value,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        value=value,
        label=label,
        value_type="DATE",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_time(
    value,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        value=value,
        label=label,
        value_type="TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_datetime(
    value,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        value=value,
        label=label,
        value_type="DATE_TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_multiline(
    value,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        value=value,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_int_secret(
    value,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "SECRET",
        value=value,
        label=label,
        value_type="INT",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_date_secret(
    value,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "SECRET",
        value=value,
        label=label,
        value_type="DATE",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_time_secret(
    value,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "SECRET",
        value=value,
        label=label,
        value_type="TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_datetime_secret(
    value,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "SECRET",
        value=value,
        label=label,
        value_type="DATE_TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def simple_variable_multiline_secret(
    value,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "SECRET",
        value=value,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_string_with_predefined_options(
    options,
    default=None,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=default,
        label=label,
        value_type="STRING",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_int_with_predefined_options(
    options,
    default=None,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=default,
        label=label,
        value_type="INT",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_date_with_predefined_options(
    options,
    default=None,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=default,
        label=label,
        value_type="DATE",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_time_with_predefined_options(
    options,
    default=None,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=default,
        label=label,
        value_type="TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_datetime_with_predefined_options(
    options,
    default=None,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=default,
        label=label,
        value_type="DATE_TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_multiline_with_predefined_options(
    options,
    default=None,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=default,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_string_with_predefined_options_array(
    options,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="STRING",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_int_with_predefined_options_array(
    options,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="INT",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_date_with_predefined_options_array(
    options,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="DATE",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_time_with_predefined_options_array(
    options,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="TIME",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_datetime_with_predefined_options_array(
    options,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="DATE_TIME",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_multiline_with_predefined_options_array(
    options,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_string_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="STRING",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_int_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="INT",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_date_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="DATE",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_time_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_datetime_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="DATE_TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_multiline_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_string_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="STRING",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_int_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="INT",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_date_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="DATE",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_time_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="TIME",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_datetime_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="DATE_TIME",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )


def variable_multiline_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        task=task,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
    )
