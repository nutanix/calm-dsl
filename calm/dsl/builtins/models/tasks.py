from .entity import EntityType


# Task


class TaskType(EntityType):
    __schema_name__ = "Task"
    __openapi_type__ = "app_tasks"


def task(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return TaskType(name, bases, kwargs)


Task = task()