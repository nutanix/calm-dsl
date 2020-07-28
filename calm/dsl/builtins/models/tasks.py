from .entity import EntityType


# Project


class TaskType(EntityType):
    __schema_name__ = "Task"
    __openapi_type__ = "app_tasks"


def task(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return ProjectType(name, bases, kwargs)


Task = task()