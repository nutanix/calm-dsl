import re

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .task_input import _task_input


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

        if cdict.get("options", None):
            options = cdict["options"]
            # Only EScript/HTTP request info needed for dynamically fetching options
            if options["type"] == "PREDEFINED":
                del options["attrs"]
            else:
                del options["choices"]  # Choices are only for PREDEFINED Type

        return cdict


class VariableValidator(PropertyValidator, openapi_type="app_variable"):
    __default__ = None
    __kind__ = VariableType


def _var(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return VariableType(name, bases, kwargs)


Variable = _var()


def setvar(name, value, type_="LOCAL", **kwargs):

    kwargs["name"] = name
    if value is not None:
        kwargs["value"] = value
    kwargs["type"] = type_

    return VariableType(name, (Variable,), kwargs)


def simple_variable(
    value,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    kwargs = {"is_hidden": is_hidden, "is_mandatory": is_mandatory}
    editables = {}
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
        if validate_regex and regex and value:
            regex_result = re.match(regex, value)
            if not regex_result:
                raise ValueError(
                    "Value '{}' doesn't match with specified regex '{}'".format(
                        value, regex
                    )
                )

        regex = {"value": regex, "should_validate": validate_regex}
        kwargs["regex"] = regex
    if description is not None:
        kwargs["description"] = description

    return setvar(name, value, **kwargs)


def simple_variable_secret(
    value,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    kwargs = {"is_hidden": is_hidden, "is_mandatory": is_mandatory}
    editables = {}
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
        if validate_regex and regex and value:
            regex_result = re.match(regex, value)
            if not regex_result:
                raise ValueError(
                    "Value '{}' doesn't match with specified regex '{}'".format(
                        value, regex
                    )
                )

        regex = {"value": regex, "should_validate": validate_regex}
        kwargs["regex"] = regex
    if description is not None:
        kwargs["description"] = description
    return setvar(name, value, type_="SECRET", **kwargs)


def _advanced_variable(
    type_,
    name=None,
    value="",
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
    description="",
):
    kwargs = {"name": name, "value": value, "type_": type_}
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
        task_attrs = task.compile().get("attrs")
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
        task_attrs["type"] = task_type
        kwargs["type_"] = task_type + "_" + type_
        kwargs["options"] = {"type": task_type, "attrs": task_attrs}
    if value_type is not None:
        value_type = value_type.upper()
        if value_type not in VARIABLE_VALUE_TYPES.values():
            raise ValueError(
                "Value type for variable "
                + (name or "")
                + ", is not valid, Expected one of"
                + " {}, got {}".format(list(VARIABLE_VALUE_TYPES.values()), value_type)
            )
        kwargs["value_type"] = value_type
    if data_type is not None:
        data_type = data_type.upper()
        if data_type not in VARIABLE_DATA_TYPES.values():
            raise ValueError(
                "Data type for variable "
                + (name or "")
                + ", is not valid, Expected one of"
                + " {}, got {}".format(list(VARIABLE_DATA_TYPES.values()), data_type)
            )
        kwargs["data_type"] = data_type
    if regex is not None:
        if not isinstance(regex, str):
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
            if validate_regex and regex:
                regex_result = re.match(regex["value"], choice)
                if not regex_result:
                    raise ValueError(
                        "Option '{}' doesn't match with specified regex '{}'".format(
                            choice, regex["value"]
                        )
                    )

            choices.append(choice)
        if isinstance(value, list) and data_type == "LIST":
            for val in value:
                if not isinstance(val, str):
                    raise TypeError(
                        "Expected list of string defaults for variable "
                        + (name or "")
                        + ", got {}".format(type(val))
                    )
                if val not in choices:
                    raise TypeError(
                        "Default value for variable array with options "
                        + (name or "")
                        + ", contains {}, which is not one of the options".format(val)
                    )
            value = ",".join(value)
            kwargs["value"] = value
        if value is None and len(choices) > 0:
            value = choices[0]
            kwargs["value"] = value
        if data_type != "LIST" and value not in choices:
            raise TypeError(
                "Default value for variable with options "
                + (name or "")
                + ", is {}, which is not one of the options".format(value)
            )
        options = {"type": "PREDEFINED", "choices": choices}
        kwargs["options"] = options
    else:
        # If options are None, just regex validate the value
        if validate_regex and regex and value:
            regex_result = re.match(regex["value"], value)
            if not regex_result:
                raise ValueError(
                    "Value '{}' doesn't match with specified regex '{}'".format(
                        value, regex["value"]
                    )
                )
    if is_hidden is not None:
        kwargs["is_hidden"] = bool(is_hidden)
    if is_mandatory is not None:
        kwargs["is_mandatory"] = bool(is_mandatory)
    if description is not None:
        kwargs["description"] = description

    return setvar(**kwargs)


def simple_variable_int(
    value,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=value,
        label=label,
        value_type="INT",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_date(
    value,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=value,
        label=label,
        value_type="DATE",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_time(
    value,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=value,
        label=label,
        value_type="TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_datetime(
    value,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=value,
        label=label,
        value_type="DATE_TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_multiline(
    value,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=value,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_int_secret(
    value,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "SECRET",
        name=name,
        value=value,
        label=label,
        value_type="INT",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_date_secret(
    value,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "SECRET",
        name=name,
        value=value,
        label=label,
        value_type="DATE",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_time_secret(
    value,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "SECRET",
        name=name,
        value=value,
        label=label,
        value_type="TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_datetime_secret(
    value,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "SECRET",
        name=name,
        value=value,
        label=label,
        value_type="DATE_TIME",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def simple_variable_multiline_secret(
    value,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "SECRET",
        name=name,
        value=value,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="BASE",
        regex=regex,
        validate_regex=validate_regex,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
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
    description="",
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
        description=description,
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
    description="",
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
        description=description,
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
    description="",
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
        description=description,
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
    description="",
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
        description=description,
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
    description="",
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
        description=description,
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
    description="",
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
        description=description,
    )


def variable_string_with_predefined_options_array(
    options,
    defaults=None,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=defaults,
        label=label,
        value_type="STRING",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def variable_int_with_predefined_options_array(
    options,
    defaults=None,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=defaults,
        label=label,
        value_type="INT",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def variable_date_with_predefined_options_array(
    options,
    defaults=None,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=defaults,
        label=label,
        value_type="DATE",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def variable_time_with_predefined_options_array(
    options,
    defaults=None,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=defaults,
        label=label,
        value_type="TIME",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def variable_datetime_with_predefined_options_array(
    options,
    defaults=None,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=defaults,
        label=label,
        value_type="DATE_TIME",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def variable_multiline_with_predefined_options_array(
    options,
    defaults=None,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    runtime=False,
    description="",
):
    return _advanced_variable(
        "LOCAL",
        name=name,
        value=defaults,
        label=label,
        value_type="MULTILINE_STRING",
        data_type="LIST",
        regex=regex,
        validate_regex=validate_regex,
        options=options,
        is_hidden=is_hidden,
        is_mandatory=is_mandatory,
        runtime=runtime,
        description=description,
    )


def variable_string_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_int_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_date_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_time_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_datetime_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_multiline_with_options_from_task(
    task,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_string_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_int_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=r"^[\d]*$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_date_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_time_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=r"^[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_datetime_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=r"^((0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/[12]\d{3})((T)|(\s-\s))[\d]{2}:[\d]{2}(:[0-5]\d)?$",
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


def variable_multiline_with_options_from_task_array(
    task,
    name=None,
    label=None,
    regex=None,
    validate_regex=False,
    is_hidden=False,
    is_mandatory=False,
    description="",
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
        runtime=True,
        description=description,
    )


class CalmVariable:
    def __new__(
        cls,
        value,
        name=None,
        label=None,
        regex=None,
        validate_regex=False,
        is_hidden=False,
        is_mandatory=False,
        runtime=False,
        description="",
    ):
        return simple_variable(
            value,
            name=name,
            label=label,
            regex=regex,
            validate_regex=validate_regex,
            is_hidden=is_hidden,
            is_mandatory=is_mandatory,
            runtime=runtime,
            description=description,
        )

    class Simple:
        def __new__(
            cls,
            value,
            name=None,
            label=None,
            regex=None,
            validate_regex=False,
            is_hidden=False,
            is_mandatory=False,
            runtime=False,
            description="",
        ):
            return simple_variable(
                value,
                name=name,
                label=label,
                regex=regex,
                validate_regex=validate_regex,
                is_hidden=is_hidden,
                is_mandatory=is_mandatory,
                runtime=runtime,
                description=description,
            )

        string = simple_variable
        int = simple_variable_int
        date = simple_variable_date
        time = simple_variable_time
        datetime = simple_variable_datetime
        multiline = simple_variable_multiline

        class Secret:
            def __new__(
                cls,
                value,
                name=None,
                label=None,
                regex=None,
                validate_regex=False,
                is_hidden=False,
                is_mandatory=False,
                runtime=False,
                description="",
            ):
                return simple_variable_secret(
                    value,
                    name=name,
                    label=label,
                    regex=regex,
                    validate_regex=validate_regex,
                    is_hidden=is_hidden,
                    is_mandatory=is_mandatory,
                    runtime=runtime,
                    description=description,
                )

            string = simple_variable_secret
            int = simple_variable_int_secret
            date = simple_variable_date_secret
            time = simple_variable_time_secret
            datetime = simple_variable_datetime_secret
            multiline = simple_variable_multiline_secret

    class WithOptions:
        def __new__(
            cls,
            options,
            default=None,
            name=None,
            label=None,
            regex=None,
            validate_regex=False,
            is_hidden=False,
            is_mandatory=False,
            runtime=False,
            description="",
        ):
            return variable_string_with_predefined_options(
                options,
                default=default,
                name=name,
                label=label,
                regex=regex,
                validate_regex=validate_regex,
                is_hidden=is_hidden,
                is_mandatory=is_mandatory,
                runtime=runtime,
                description=description,
            )

        class Predefined:
            def __new__(
                cls,
                options,
                default=None,
                name=None,
                label=None,
                regex=None,
                validate_regex=False,
                is_hidden=False,
                is_mandatory=False,
                runtime=False,
                description="",
            ):
                return variable_string_with_predefined_options(
                    options,
                    default=default,
                    name=name,
                    label=label,
                    regex=regex,
                    validate_regex=validate_regex,
                    is_hidden=is_hidden,
                    is_mandatory=is_mandatory,
                    runtime=runtime,
                    description=description,
                )

            string = variable_string_with_predefined_options
            int = variable_int_with_predefined_options
            date = variable_date_with_predefined_options
            time = variable_time_with_predefined_options
            datetime = variable_datetime_with_predefined_options
            multiline = variable_multiline_with_predefined_options

            class Array:
                def __new__(
                    cls,
                    options,
                    defaults=None,
                    name=None,
                    label=None,
                    regex=None,
                    validate_regex=False,
                    is_hidden=False,
                    is_mandatory=False,
                    runtime=False,
                    description="",
                ):
                    return variable_string_with_predefined_options_array(
                        options,
                        defaults=defaults,
                        name=name,
                        label=label,
                        regex=regex,
                        validate_regex=validate_regex,
                        is_hidden=is_hidden,
                        is_mandatory=is_mandatory,
                        runtime=runtime,
                        description=description,
                    )

                string = variable_string_with_predefined_options_array
                int = variable_int_with_predefined_options_array
                date = variable_date_with_predefined_options_array
                time = variable_time_with_predefined_options_array
                datetime = variable_datetime_with_predefined_options_array
                multiline = variable_multiline_with_predefined_options_array

        class FromTask:
            def __new__(
                cls,
                task,
                name=None,
                label=None,
                regex=None,
                validate_regex=False,
                is_hidden=False,
                is_mandatory=False,
                description="",
            ):
                return variable_string_with_options_from_task(
                    task,
                    name=name,
                    label=label,
                    regex=regex,
                    validate_regex=validate_regex,
                    is_hidden=is_hidden,
                    is_mandatory=is_mandatory,
                    description=description,
                )

            string = variable_string_with_options_from_task
            int = variable_int_with_options_from_task
            date = variable_date_with_options_from_task
            time = variable_time_with_options_from_task
            datetime = variable_datetime_with_options_from_task
            multiline = variable_multiline_with_options_from_task

            class Array:
                def __new__(
                    cls,
                    task,
                    name=None,
                    label=None,
                    regex=None,
                    validate_regex=False,
                    is_hidden=False,
                    is_mandatory=False,
                    description="",
                ):
                    return variable_string_with_options_from_task_array(
                        task,
                        name=name,
                        label=label,
                        regex=regex,
                        validate_regex=validate_regex,
                        is_hidden=is_hidden,
                        is_mandatory=is_mandatory,
                        description=description,
                    )

                string = variable_string_with_options_from_task_array
                int = variable_int_with_options_from_task_array
                date = variable_date_with_options_from_task_array
                time = variable_time_with_options_from_task_array
                datetime = variable_datetime_with_options_from_task_array
                multiline = variable_multiline_with_options_from_task_array


class RunbookVariable(CalmVariable):
    class TaskInput:
        def __new__(cls, *args, **kwargs):
            return _task_input(*args, **kwargs)
