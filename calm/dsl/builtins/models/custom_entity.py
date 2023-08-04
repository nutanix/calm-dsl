import json

from calm.dsl.log import get_logging_handle
from .variable import CalmVariable
from .constants import HIDDEN_SUFFIX

LOG = get_logging_handle(__name__)


SimpleVariableTypeMap = {
    "STRING": CalmVariable.Simple.string,
    "INT": CalmVariable.Simple.int,
    "BOOLEAN": CalmVariable.Simple.boolean,
    "DICT": CalmVariable.Simple.dictionary,
}

SecretVariableTypeMap = {
    "STRING": CalmVariable.Simple.Secret.string,
    "INT": CalmVariable.Simple.Secret.int,
}

PredefinedOptionsVariableTypeMap = {
    "STRING": CalmVariable.WithOptions.Predefined.string,
    "INT": CalmVariable.WithOptions.Predefined.int,
}


class CustomEntity(object):
    """Base Class for Custom Entities"""

    name = "Custom Entity"
    FIELD_MAP = {}
    DUPLICATE_KEY_MAP = (
        {}
    )  # This has duplicate keys as field map, this ensure user only provide value once which will be added to different variables.

    def __init__(self, **kwargs):

        self.field_values = dict()
        for field_name in kwargs:
            if field_name not in self.FIELD_MAP or field_name.endswith(HIDDEN_SUFFIX):
                raise Exception(
                    "field {} is not mapped as a property under {}".format(
                        field_name, self.name
                    )
                )
            var_name = self.FIELD_MAP[field_name]
            self.field_values[var_name] = kwargs.get(field_name)

    def pre_validate(self, account):
        """
        Base pre validation method, handles any prevalidation at base level.
        Args:
            account (Ref.Account): Object of Calm Ref Accounts
        """

    def validate(self, account, action_variable_list, task_name_modified, inargs):
        """validate the given attributes with the variable list of chosen action
        Args:
            account (ref): account ref object
            action_variable_list ([dict]): action variable list from which it needs to be validated
            task_name_modified (string): prefix of variable name
            inargs ([dict]): Array dictionary into which validated variables need to be appended
        Returns:
            [dict]
        """

        self.pre_validate(account)

        # Add field values for duplicate variable
        for field, val in self.DUPLICATE_KEY_MAP.items():
            if self.FIELD_MAP[field] in self.field_values:
                self.field_values[val] = self.field_values[self.FIELD_MAP[field]]

        reverse_field_map = dict((v, k) for k, v in self.FIELD_MAP.items())
        for var in action_variable_list:

            # This removes the task name prefix added to action variables
            modified_var_name = var["name"][len(task_name_modified) + 2 :]

            if (
                modified_var_name not in reverse_field_map
                and modified_var_name not in self.DUPLICATE_KEY_MAP.values()
            ):
                continue

            if (
                modified_var_name not in self.field_values
                or self.field_values[modified_var_name] is None
            ):
                if var.get("is_mandatory", False):
                    raise ValueError(
                        "{} is a mandatory field for {}, Please provide value for this".format(
                            reverse_field_map[modified_var_name], self.name
                        )
                    )
                continue

            val = self.field_values[modified_var_name]
            if var["type"] == "SECRET":
                variable = SecretVariableTypeMap[var["val_type"]](
                    value=str(val),
                    name=var["name"],
                    regex=var["regex"]["value"] if var["regex"] else None,
                    validate_regex=var["regex"]["should_validate"]
                    if var["regex"]
                    else False,
                    is_hidden=var["is_hidden"],
                    is_mandatory=var["is_mandatory"],
                    label=var.get("label"),
                )
            elif var["options"]:
                variable = PredefinedOptionsVariableTypeMap[var["val_type"]](
                    options=var["options"]["choices"],
                    default=str(val),
                    name=var["name"],
                    regex=var["regex"]["value"] if var["regex"] else None,
                    validate_regex=var["regex"]["should_validate"]
                    if var["regex"]
                    else False,
                    is_hidden=var["is_hidden"],
                    is_mandatory=var["is_mandatory"],
                    label=var.get("label"),
                )
            else:
                if var["val_type"] == "DICT" and not isinstance(val, str):
                    try:
                        val = json.dumps(val)
                    except Exception as exc:
                        raise ValueError(
                            "var {} value {} is not json serializable: failing with error {}".format(
                                var["name"], val, exc
                            )
                        )
                variable = SimpleVariableTypeMap[var["val_type"]](
                    value=str(val),
                    name=var["name"],
                    type_=var["type"],
                    data_type=var["data_type"],
                    regex=var["regex"]["value"] if var["regex"] else None,
                    validate_regex=var["regex"]["should_validate"]
                    if var["regex"]
                    else False,
                    is_hidden=var["is_hidden"],
                    is_mandatory=var["is_mandatory"],
                    label=var.get("label"),
                    attrs=var["attrs"] if var["attrs"] else None,
                )

            inargs.append(variable)


class OutputVariables(object):
    """Base Class for RT Actions Output variables of NDB Provider"""

    name = "OutputVariables"
    FIELD_MAP = {}

    def __init__(self, **kwargs):
        self.field_values = dict()
        for field in kwargs:
            if field not in self.FIELD_MAP:
                raise Exception(
                    "field {} is not mapped as a output variable under {}".format(
                        field, self.name
                    )
                )
            if kwargs.get(field):
                self.field_values[self.FIELD_MAP[field]] = kwargs.get(field)

        # Adding RHS side as default output variable name if user hasn't provided.
        for key, value in self.FIELD_MAP.items():
            if value not in self.field_values and key != value:
                self.field_values[value] = key
