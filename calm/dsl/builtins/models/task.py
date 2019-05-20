import uuid

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .ref import RefType
from .variable import setvar


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


def exec_http(
    method,
    url,
    body=None,
    headers=None,
    auth=None,
    content_type=None,
    timeout=120,
    verify=False,
    retries=0,
    retry_interval=10,
    status_mapping=None,
    response_paths=None,
    name=None,
    target=None,
):
    """
    Defines a HTTP Task.

    Args:
        method (str): Request method (GET, PUT, POST, DELETE, etc.)
        url (str): Request URL (https://example.com/dummy_url)
        body (str): Request body
        headers (dict): Request headers
        auth (Credential): Credential object
        content_type (string): Request Content-Type (application/json, application/xml, etc.)
        timeout (int): Request timeout in seconds (Default: 120)
        verify (bool): TLS verify (Default: False)
        retries (int): Number of times to retry this request if it fails. (Default: 0)
        retry_interval (int): Time to wait in seconds between retries (Default: 10)
        status_mapping (dict): Mapping of  Response status code (int) to
                               task status (True: success, False: Failure)
        response_paths (dict): Mapping of variable name (str) to path in response (str)
        name (str): Task name
        target (Ref): Target entity that this task runs under.
    Returns:
        (Task): HTTP Task
    """
    # TODO: Auth
    kwargs = {
        "type": "HTTP",
        # "timeout_secs": "0", # TODO - fix class creation params
        # "retries": "0",
        # "state": "ACTIVE",
        "attrs": {
            "method": method,
            "url": url,
            "request_body": body,
            "auth": auth,
            "content_type": content_type,
            "timeout": timeout,
            "verify": verify,
            "retry_count": retries + 1,
            "retry_interval": retry_interval,
            "login_credential_local_reference": {
                "kind": "app_credential",
                "name": "default",  # TODO
            },
        },
    }

    if headers is not None:
        header_variables = []
        if not isinstance(headers, dict):
            raise TypeError(
                "Headers for HTTP task " + name
                or "" + " should be dictionary of strings"
            )
        for var_name, var_value in headers.items():
            if not isinstance(var_name, str):
                raise TypeError(
                    "Headers for HTTP task " + name
                    or "" + " should be dictionary of strings"
                )
            if not isinstance(var_value, str):
                raise TypeError(
                    "Headers for HTTP task " + name
                    or "" + " should be dictionary of strings"
                )
            header_variables.append(setvar(var_name, var_value))
        kwargs["header_variables"] = header_variables

    if status_mapping is not None:
        if not isinstance(status_mapping, dict):
            raise TypeError(
                "Status mapping for HTTP task " + name
                or "" + " should be dictionary of int keys and boolean values"
            )
        expected_response = []
        for code, state in status_mapping.items():
            if not isinstance(code, int):
                raise TypeError(
                    "Status mapping for HTTP task " + name
                    or "" + " should be dictionary of int keys and boolean values"
                )
            if not isinstance(state, bool):
                raise TypeError(
                    "Status mapping for HTTP task " + name
                    or "" + " should be dictionary of int keys and boolean values"
                )
            expected_response.append(
                {"status": "SUCCESS" if state else "FAILURE", "code": code}
            )
        kwargs["expected_response_params"] = expected_response

    if response_paths is not None:
        if not isinstance(response_paths, dict):
            raise TypeError(
                "Response paths for HTTP task " + name
                or "" + " should be dictionary of strings"
            )
        for prop, path in response_paths.items():
            if not isinstance(prop, int):
                raise TypeError(
                    "Response paths for HTTP task " + name
                    or "" + " should be dictionary of strings"
                )
            if not isinstance(path, bool):
                raise TypeError(
                    "Response paths for HTTP task " + name
                    or "" + " should be dictionary of strings"
                )
            expected_response.append(
                {"status": "SUCCESS" if state else "FAILURE", "code": code}
            )
        kwargs["response_paths"] = response_paths

    return _task_create(**kwargs)


def _deployment_scaling_create(target, scaling_type, scaling_count, name=None):
    if not target:
        raise ValueError("A target is required for deployment scaling task")
    if not isinstance(target, RefType) and isinstance(target, EntityType):
        target = target.get_ref()
    if not target.kind == "app_deployment":
        raise ValueError(
            "Target for deployment scaling cannot be {}".format(target.kind)
        )

    kwargs = {
        "name": name
        if name is not None
        else "{}_task_for_{}__{}".format(
            scaling_type, target.name, str(uuid.uuid4())[:8]
        ),
        "type": "SCALING",
        # "timeout_secs": "0", # TODO - fix class creation params
        # "retries": "0",
        # "state": "ACTIVE",
        "attrs": {
            "scaling_type": scaling_type,
            "scaling_count": str(scaling_count),
            "login_credential_local_reference": {
                "kind": "app_credential",
                "name": "default",  # TODO
            },
        },
        "target_any_local_reference": target,
    }

    return _task_create(**kwargs)


def deployment_scaleout(target, count, name=None):
    """
    Defines a deployment scale out task
    Args:
        target (Ref): Target entity for scale out
        count (str): scaling_count
        name (str): Name for this task
    Returns:
        (Task): Deployment scale out task
    """
    return _deployment_scaling_create(target, "SCALEOUT", count, name=name)


def deployment_scalein(target, count, name=None):
    """
    Defines a deployment scale in task
    Args:
        target (Ref): Target entity for scale in
        count (str): scaling_count
        name (str): Name for this task
    Returns:
        (Task): Deployment scale in task
    """
    return _deployment_scaling_create(target, "SCALEIN", count, name=name)
