from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template
from calm.dsl.builtins import VariableType, TaskType


def render_variable_template(cls):

    if not isinstance(cls, VariableType):
        raise TypeError("{} is not of type {}".format(cls, VariableType))

    user_attrs = cls.get_user_attrs()
    var_val_type = getattr(cls, "value_type", "STRING")
    var_type = ""
    schema_file = None

    if not cls.options:
        var_type = "simple"

    if cls.regex:
        regex = cls.regex.get_dict()
        user_attrs["regex"] = regex.get("value", None)
        user_attrs["validate_regex"] = regex.get("should_validate", False)

    else:
        user_attrs["regex"] = None
        user_attrs["validate_regex"] = False

    if cls.editables:
        user_attrs["runtime"] = cls.editables["value"]
    else:
        user_attrs["runtime"] = False

    user_attrs["name"] = cls.__name__

    if var_type == "simple":
        is_secret = True if user_attrs["type"] == "SECRET" else False

        if is_secret:
            if var_val_type == "STRING":
                schema_file = "var_simple_secret_string.py.jinja2"
            elif var_val_type == "INT":
                schema_file = "var_simple_secret_int.py.jinja2"
            elif var_val_type == "TIME":
                schema_file = "var_simple_secret_time.py.jinja2"
            elif var_val_type == "DATE":
                schema_file = "var_simple_secret_date.py.jinja2"
            elif var_val_type == "DATE_TIME":
                schema_file = "var_simple_secret_datetime.py.jinja2"
            elif var_val_type == "MULTILINE_STRING":
                user_attrs["value"] = repr(user_attrs["value"])
                schema_file = "var_simple_secret_multiline.py.jinja2"

        else:
            if var_val_type == "STRING":
                schema_file = "var_simple_string.py.jinja2"
            elif var_val_type == "INT":
                schema_file = "var_simple_int.py.jinja2"
            elif var_val_type == "TIME":
                schema_file = "var_simple_time.py.jinja2"
            elif var_val_type == "DATE":
                schema_file = "var_simple_date.py.jinja2"
            elif var_val_type == "DATE_TIME":
                schema_file = "var_simple_datetime.py.jinja2"
            elif var_val_type == "MULTILINE_STRING":
                user_attrs["value"] = repr(user_attrs["value"])
                schema_file = "var_simple_multiline.py.jinja2"
          

    else:
        data_type = cls.data_type
        options = cls.options.get_dict()
        option_type = options.get("type", "PREDEFINED")

        if option_type == "PREDEFINED":
            user_attrs["choices"] = options.get("choices", [])

            if data_type == "BASE":
                if var_val_type == "STRING":
                    schema_file = "var_with_options_predefined_string.py.jinja2"
                elif var_val_type == "INT":
                    schema_file = "var_with_options_predefined_int.py.jinja2"
                elif var_val_type == "DATE":
                    schema_file = "var_with_options_predefined_date.py.jinja2"
                elif var_val_type == "TIME":
                    schema_file = "var_with_options_predefined_time.py.jinja2"
                elif var_val_type == "DATE_TIME":
                    schema_file = "var_with_options_predefined_datetime.py.jinja2"
                elif var_val_type == "MULTILINE_STRING":
                    user_attrs["value"] = repr(user_attrs["value"])
                    schema_file = "var_with_options_predefined_multiline.py.jinja2"

            else:
                defaults = cls.value
                user_attrs["value"] = defaults.split(",")
                if var_val_type == "STRING":
                    schema_file = "var_with_options_predefined_array_string.py.jinja2"
                elif var_val_type == "INT":
                    schema_file = "var_with_options_predefined_array_int.py.jinja2"
                elif var_val_type == "DATE":
                    schema_file = "var_with_options_predefined_array_date.py.jinja2"
                elif var_val_type == "TIME":
                    schema_file = "var_with_options_predefined_array_time.py.jinja2"
                elif var_val_type == "DATE_TIME":
                    schema_file = "var_with_options_predefined_array_datetime.py.jinja2"
                elif var_val_type == "MULTILINE_STRING":
                    user_attrs["value"] = repr(user_attrs["value"])
                    schema_file = "var_with_options_predefined_array_multiline.py.jinja2"

        else:
            options.pop("choices", None)
            task = TaskType.decompile(options)
            user_attrs["value"] = render_task_template(task)

            if data_type == "BASE":
                if var_val_type == "STRING":
                    schema_file = "var_with_options_fromTask_string.py.jinja2"
                elif var_val_type == "INT":
                    schema_file = "var_with_options_fromTask_int.py.jinja2"
                elif var_val_type == "DATE":
                    schema_file = "var_with_options_fromTask_date.py.jinja2"
                elif var_val_type == "TIME":
                    schema_file = "var_with_options_fromTask_time.py.jinja2"
                elif var_val_type == "DATE_TIME":
                    schema_file = "var_with_options_fromTask_datetime.py.jinja2"
                elif var_val_type == "MULTILINE_STRING":
                    user_attrs["value"] = repr(user_attrs["value"])
                    schema_file = "var_with_options_fromTask_multiline.py.jinja2"
            else:
                if var_val_type == "STRING":
                    schema_file = "var_with_options_fromTask_array_string.py.jinja2"
                elif var_val_type == "INT":
                    schema_file = "var_with_options_fromTask_array_int.py.jinja2"
                elif var_val_type == "DATE":
                    schema_file = "var_with_options_fromTask_array_date.py.jinja2"
                elif var_val_type == "TIME":
                    schema_file = "var_with_options_fromTask_array_time.py.jinja2"
                elif var_val_type == "DATE_TIME":
                    schema_file = "var_with_options_fromTask_array_datetime.py.jinja2"
                elif var_val_type == "MULTILINE_STRING":
                    schema_file = "var_with_options_fromTask_array_multiline.py.jinja2"

    if not schema_file:
        raise Exception("Unknown variable type")

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
