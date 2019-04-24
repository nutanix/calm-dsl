import uuid

from .entity import EntityType, Entity
from .validator import PropertyValidator


# Task


class TaskType(EntityType):
    __schema_name__ = "Task"
    __openapi_type__ = "app_task"


class TaskValidator(PropertyValidator, openapi_type="app_task"):
    __default__ = None
    __kind__ = TaskType


def _task(**kwargs):
    name = getattr(TaskType, "__schema_name__")
    bases = (Entity,)
    return TaskType(name, bases, kwargs)


Task = _task()


def _task_create(**kwargs):
    name = getattr(TaskType, "__schema_name__") + "_" + str(uuid.uuid4())[:8]
    name = kwargs.get("name", kwargs.get("__name__", name))
    bases = (Task,)
    return TaskType(name, bases, kwargs)


def exec_ssh(script, name=None):

    kwargs = {
        "type": "EXEC",
        # "timeout_secs": "0", # TODO - fix class creation params
        # "retries": "0",
        # "state": "ACTIVE",
        "attrs": {
            "script_type": "sh",
            "script": script,
            "login_credential_local_reference": {
                "kind": "app_credential",
                "name": "Credential",  # TODO
            },
        },
    }
    if name is not None:
        kwargs["name"] = name

    return _task_create(**kwargs)


def dag(name=None, child_tasks=None, edges=None):
    """
    Create a DAG task
    Args:
        name (str): Name for the task
        child_tasks (list [Task]): Child tasks within this dag
        edges (list [tuple (ref, ref)]): List of tuples of ref(Task).
                                         Each element denotes an edge from
                                         first task to the second.
    Returns:
        (Task): DAG task
    """
    dag_edges = []
    for edge in edges or []:
        if len(edge) != 2:
            raise ValueError("DAG edges require a tuple of two task references")
        for task_ref in edge:
            if not getattr(task_ref, "__kind__") == "app_ref":
                raise ValueError("{} is not a valid task reference".format(task_ref))
        from_ref = edge[0]
        to_ref = edge[1]
        dag_edges.append({"from_task_reference": from_ref, "to_task_reference": to_ref})

    # This follows UI naming convention for runbooks
    name = name or str(uuid.uuid4())[:8] + "_dag"
    kwargs = {
        "name": name,
        "child_tasks_local_reference_list": [
            task.get_ref() for task in child_tasks or []
        ],
        "attrs": {"edges": dag_edges},
        "type": "DAG",
    }

    return _task_create(**kwargs)
