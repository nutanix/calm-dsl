from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import VariableType, CalmVariable, CalmTask


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

    import pdb; pdb.set_trace()

    if var_type == "simple":
        is_secret = True if user_attrs["type"] == "SECRET" else False

        if is_secret:
            if var_val_type == "STRING":
                schema_file = "var_simple_secret_string.py.jinja2"
        
        else:
            if var_val_type == "STRING":
                schema_file = "var_simple_string.py.jinja2"

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
var14 = CalmVariable.WithOptions.Predefined.int(
    ["0", "1"],
    label="var14_label",
    regex="^[0-9]+$",
    validate_regex=True,
    runtime=True,
)
var20 = CalmVariable.WithOptions.Predefined.Array.int(
    ["0", "1"],
    label="var20_label",
    regex="^[0-9]+$",
    validate_regex=True,
    runtime=True,
)
var26 = CalmVariable.WithOptions.FromTask.int(
    CalmTask.Exec.escript(script="print '0'"), label="var26_label", validate_regex=True,
)
var32 = CalmVariable.WithOptions.FromTask.Array.int(
    CalmTask.Exec.escript(script="print '0,1'"),
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

print(render_variable_template(var2))
