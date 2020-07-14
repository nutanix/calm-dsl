from .entity import EntityType, Entity
from .validator import PropertyValidator
from .constants import TASK_INPUT


# TaskInput


class TaskInputType(EntityType):
    __schema_name__ = "TaskInput"
    __openapi_type__ = "task_input"


class TaskInputValidator(PropertyValidator, openapi_type="task_input"):
    __default__ = None
    __kind__ = TaskInputType


def _task_input(*args, **kwargs):
    name = kwargs.get("name", None)
    input_type = kwargs.get("input_type", None)
    options = kwargs.get("options", [])
    if not name:
        if len(args) > 0 and isinstance(args[0], str):
            kwargs["name"] = args[0]
            name = args[0]
        else:
            raise ValueError("Input name is required property")
    if input_type is None:
        kwargs["input_type"] = TASK_INPUT.TYPE.TEXT
    elif input_type not in TASK_INPUT.VALID_TYPES:
        raise ValueError(
            "Input type is not valid. Supported input types are {}.".format(
                TASK_INPUT.VALID_TYPES
            )
        )

    if (
        input_type == TASK_INPUT.TYPE.SELECT
        or input_type == TASK_INPUT.TYPE.SELECTMULTIPLE
    ):
        if len(options) == 0:
            raise ValueError(
                "There must be atleast one option for input of type {}.".format(
                    input_type
                )
            )
    bases = (Entity,)
    return TaskInputType(name, bases, kwargs)
