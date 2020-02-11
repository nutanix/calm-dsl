from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template
from calm.dsl.builtins import VariableType, CalmVariable, CalmTask, TaskType


def render_variable_template(cls):

    if not isinstance(cls, VariableType):
        raise TypeError("{} is not of type {}".format(cls, VariableType))

    user_attrs = cls.get_user_attrs()
    var_val_type = getattr(cls, "value_type", "STRING")
    var_type = ""

    if not cls.options:
        var_type = "simple"

    if cls.regex:
        regex = cls.regex.compile(cls)
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
        
        else:
            if var_val_type == "STRING":
                schema_file = "var_simple_string.py.jinja2"
    
    else:
        data_type = cls.data_type
        options = cls.options.compile(cls)
        option_type = options.get("type", "PREDEFINED")

        if option_type == "PREDEFINED":
            user_attrs["choices"] = options.get("choices", [])

            if data_type == "BASE":
                if var_val_type == "STRING":
                    schema_file = "var_with_options_predefined.py.jinja2"
            
            else:
                defaults = cls.value
                user_attrs["value"] = defaults.split(",")
                if var_val_type == "STRING":
                    schema_file = "var_with_options_predefined_array.py.jinja2"
        
        else:
            choices = options.pop("choices", None)
            task = TaskType.decompile(options)
            user_attrs["value"] = render_task_template(task)

            if data_type == "BASE":
                if var_val_type == "STRING":
                    schema_file = "var_with_options_fromTask.py.jinja2"
            
            else:
                if var_val_type == "STRING":
                    schema_file = "var_with_options_fromTask_array.py.jinja2"
                
    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()


var3 = CalmVariable.Simple.int(
    "42",
    label="var3_label",
    validate_regex=True,
    runtime=True,
    is_hidden=True,
    is_mandatory=True,
)
var2 = CalmVariable.Simple.Secret(
    "var2_val",
    label="var2_label",
    regex="^[a-zA-Z0-9_]+$",
    validate_regex=True,
    is_hidden=True,
    is_mandatory=True,
)
var13 = CalmVariable.WithOptions(
        ["var13_val1", "var13_val2"],
        default="var13_val1",
        label="var13_label",
        regex="^[a-zA-Z0-9_]+$",
        validate_regex=True,
        runtime=True,
    )
var19 = CalmVariable.WithOptions.Predefined.Array(
        ["var19_val1", "var19_val2"],
        defaults=["var19_val1", "var19_val2"],
        label="var19_label",
        regex="^[a-zA-Z0-9_]+$",
        validate_regex=True,
        runtime=True,
    )
var25 = CalmVariable.WithOptions.FromTask(
        CalmTask.HTTP.get(
            "https://jsonplaceholder.typicode.com/posts/1",
            # Headers in HTTP variables are bugged:
            # https://jira.nutanix.com/browse/CALM-13724
            # headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            response_paths={"var25": "$.title"},
        ),
        label="var25_label",
    )

var31 = CalmVariable.WithOptions.FromTask.Array(
        CalmTask.HTTP.get(
            "https://jsonplaceholder.typicode.com/posts/1",
            # Headers in HTTP variables are bugged:
            # https://jira.nutanix.com/browse/CALM-13724
            # headers={"Content-Type": "application/json"},
            content_type="application/json",
            verify=True,
            status_mapping={200: True},
            response_paths={"var31": "$.title"},
        ),
        label="var31_label",
    )
var33 = CalmVariable.Simple("sample")

var1 = CalmVariable.Simple(
        "var1_val",
        label="var1_label",
        regex="^[a-zA-Z0-9_]+$",
        validate_regex=True,
        runtime=True,
        is_mandatory=True
    )

print(render_variable_template(var31))
