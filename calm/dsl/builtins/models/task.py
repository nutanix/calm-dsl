import uuid

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .ref import RefType


# Task


class TaskType(EntityType):
    __schema_name__ = "Task"
    __openapi_type__ = "app_task"

    def compile(cls):
        cdict = super().compile()
        if (cdict.get("target_any_local_reference", None) or None) is None:
            cdict.pop("target_any_local_reference", None)
        return cdict


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


def create_call_rb(runbook, target=None, name=None):
    kwargs = {
        "name": name
        or "Call_Runbook_task_for_{}__{}".format(runbook.name, str(uuid.uuid4())[:8]),
        "type": "CALL_RUNBOOK",
        "attrs": {"runbook_reference": runbook.get_ref()},
    }
    if target is not None:
        if not isinstance(target, RefType) and isinstance(target, EntityType):
            target = target.get_ref()
        kwargs["target_any_local_reference"] = target
    else:
        main_dag = [
            task
            for task in runbook.tasks
            if task.name == runbook.main_task_local_reference.name
        ][0]
        kwargs["target_any_local_reference"] = main_dag.target_any_local_reference

    return _task_create(**kwargs)


def _exec_create(script, script_type, name=None, target=None):

    kwargs = {
        "type": "EXEC",
        # "timeout_secs": "0", # TODO - fix class creation params
        # "retries": "0",
        # "state": "ACTIVE",
        "attrs": {
            "script_type": script_type,
            "script": script,
            "login_credential_local_reference": {
                "kind": "app_credential",
                "name": "default",  # TODO
            },
        },
    }
    if name is not None:
        kwargs["name"] = name
    if target is not None:
        if not isinstance(target, RefType) and isinstance(target, EntityType):
            target = target.get_ref()
        kwargs["target_any_local_reference"] = target

    return _task_create(**kwargs)


def dag(name=None, child_tasks=None, edges=None, target=None):
    """
    Create a DAG task
    Args:
        name (str): Name for the task
        child_tasks (list [Task]): Child tasks within this dag
        edges (list [tuple (Ref, Ref)]): List of tuples of ref(Task).
                                         Each element denotes an edge from
                                         first task to the second.
        target (Ref): Target entity reference
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
    if target:
        kwargs["target_any_local_reference"] = target

    return _task_create(**kwargs)


def exec_ssh(script, name=None, target=None):
    return _exec_create(script, "sh", name=name, target=target)


def exec_escript(script, name=None, target=None):
    return _exec_create(script, "static", name=name, target=target)
