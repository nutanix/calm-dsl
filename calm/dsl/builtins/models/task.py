import uuid
import os
import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .ref import RefType
from .variable import CalmVariable
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)

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
    name = kwargs.get("name", None)
    bases = (Entity,)
    return TaskType(name, bases, kwargs)


Task = _task()


def _get_target_ref(target):
    """
    Get the target reference. Converts target to a ref if it is an entity.
    Args:
        target (Entity/Ref): Entity/Ref that is the target for this task
    Returns:
        (Ref): Target reference
    """
    if target is not None:
        if not isinstance(target, RefType) and isinstance(target, EntityType):
            target = target.get_ref()
    return target


def _task_create(**kwargs):

    name = kwargs.get("name", kwargs.pop("__name__", None))
    if name is None:
        name = "_" + getattr(TaskType, "__schema_name__") + str(uuid.uuid4())[:8]
        kwargs["name"] = name

    return _task(**kwargs)


def create_call_rb(runbook, target=None, name=None):
    kwargs = {
        "name": name
        or "Call_Runbook_task_for_{}__{}".format(runbook.name, str(uuid.uuid4())[:8]),
        "type": "CALL_RUNBOOK",
        "attrs": {"runbook_reference": runbook.get_ref()},
    }
    if target is not None:
        kwargs["target_any_local_reference"] = _get_target_ref(target)
    else:
        main_dag = [
            task
            for task in runbook.tasks
            if task.name == runbook.main_task_local_reference.name
        ][0]
        kwargs["target_any_local_reference"] = main_dag.target_any_local_reference

    return _task_create(**kwargs)


def _exec_create(
    script_type, script=None, filename=None, name=None, target=None, cred=None, depth=2
):

    if script is not None and filename is not None:
        raise ValueError(
            "Only one of script or filename should be given for exec task "
            + (name or "")
        )

    if filename is not None:
        file_path = os.path.join(
            os.path.dirname(sys._getframe(depth).f_globals.get("__file__")), filename
        )

        with open(file_path, "r") as scriptf:
            script = scriptf.read()

    if script is None:
        raise ValueError(
            "One of script or filename is required for exec task " + (name or "")
        )

    kwargs = {
        "name": name,
        "type": "EXEC",
        "attrs": {"script_type": script_type, "script": script},
    }
    if cred is not None:
        kwargs["attrs"]["login_credential_local_reference"] = _get_target_ref(cred)
    if target is not None:
        kwargs["target_any_local_reference"] = _get_target_ref(target)

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


def exec_task_ssh(
    script=None, filename=None, name=None, target=None, cred=None, depth=2
):
    return _exec_create(
        "sh",
        script=script,
        filename=filename,
        name=name,
        target=target,
        cred=cred,
        depth=depth,
    )


def exec_task_escript(script=None, filename=None, name=None, target=None, depth=2):
    return _exec_create(
        "static",
        script=script,
        filename=filename,
        name=name,
        target=target,
        depth=depth,
    )


def exec_task_powershell(
    script=None, filename=None, name=None, target=None, cred=None, depth=2
):
    return _exec_create(
        "npsscript",
        script=script,
        filename=filename,
        name=name,
        target=target,
        cred=cred,
        depth=depth,
    )


def _set_variable_create(task, variables=None):
    task.type = "SET_VARIABLE"
    eval_variables = []
    for var in variables or []:
        if not isinstance(var, str):
            raise TypeError(
                "Expected string in set variable task variables list, got {}".format(
                    type(var)
                )
            )
        eval_variables.append(var)
    task.attrs["eval_variables"] = eval_variables
    return task


def set_variable_task_ssh(
    script=None,
    filename=None,
    name=None,
    target=None,
    variables=None,
    depth=3,
    cred=None,
):
    task = exec_task_ssh(
        script=script,
        filename=filename,
        name=name,
        target=target,
        depth=depth,
        cred=cred,
    )
    return _set_variable_create(task, variables)


def set_variable_task_escript(
    script=None, filename=None, name=None, target=None, variables=None, depth=3
):
    task = exec_task_escript(
        script=script, filename=filename, name=name, target=target, depth=depth
    )
    return _set_variable_create(task, variables)


def set_variable_task_powershell(
    script=None,
    filename=None,
    name=None,
    target=None,
    variables=None,
    depth=3,
    cred=None,
):
    task = exec_task_powershell(
        script=script,
        filename=filename,
        name=name,
        target=target,
        depth=depth,
        cred=cred,
    )
    return _set_variable_create(task, variables)


def http_task_get(
    url,
    body=None,
    headers=None,
    secret_headers=None,
    credential=None,
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

    Defines a HTTP GET Task.

    Args:
        url (str): Request URL (https://example.com/dummy_url)
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
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
    return http_task(
        "GET",
        url,
        body=None,
        headers=headers,
        secret_headers=secret_headers,
        credential=credential,
        content_type=content_type,
        timeout=timeout,
        verify=verify,
        retries=retries,
        retry_interval=retry_interval,
        status_mapping=status_mapping,
        response_paths=response_paths,
        name=name,
        target=target,
    )


def http_task_post(
    url,
    body=None,
    headers=None,
    secret_headers=None,
    credential=None,
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

    Defines a HTTP POST Task.

    Args:
        url (str): Request URL (https://example.com/dummy_url)
        body (str): Request body
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
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
    return http_task(
        "POST",
        url,
        body=body,
        headers=headers,
        secret_headers=secret_headers,
        credential=credential,
        content_type=content_type,
        timeout=timeout,
        verify=verify,
        retries=retries,
        retry_interval=retry_interval,
        status_mapping=status_mapping,
        response_paths=response_paths,
        name=name,
        target=target,
    )


def http_task_put(
    url,
    body=None,
    headers=None,
    secret_headers=None,
    credential=None,
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

    Defines a HTTP PUT Task.

    Args:
        url (str): Request URL (https://example.com/dummy_url)
        body (str): Request body
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
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
    return http_task(
        "PUT",
        url,
        body=body,
        headers=headers,
        secret_headers=secret_headers,
        credential=credential,
        content_type=content_type,
        timeout=timeout,
        verify=verify,
        retries=retries,
        retry_interval=retry_interval,
        status_mapping=status_mapping,
        response_paths=response_paths,
        name=name,
        target=target,
    )


def http_task_delete(
    url,
    body=None,
    headers=None,
    secret_headers=None,
    credential=None,
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

    Defines a HTTP DELETE Task.

    Args:
        url (str): Request URL (https://example.com/dummy_url)
        body (str): Request body
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
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
    return http_task(
        "DELETE",
        url,
        body=body,
        headers=headers,
        secret_headers=secret_headers,
        credential=credential,
        content_type=content_type,
        timeout=timeout,
        verify=verify,
        retries=retries,
        retry_interval=retry_interval,
        status_mapping=status_mapping,
        response_paths=response_paths,
        name=name,
        target=target,
    )


def _header_variables_from_dict(headers, secret=False):
    variables = []
    LOG.debug("Headers for HTTP task : {}".format(headers))
    if not isinstance(headers, dict):
        raise TypeError(
            "Headers for HTTP task "
            + (headers or "")
            + " should be dictionary of strings"
        )
    for var_name, var_value in headers.items():
        if not isinstance(var_name, str):
            raise TypeError(
                "Headers for HTTP task "
                + (var_name or "")
                + " should be dictionary of strings"
            )
        if not isinstance(var_value, str):
            raise TypeError(
                "Headers for HTTP task "
                + (var_value or "")
                + " should be dictionary of strings"
            )
        if secret:
            variable = CalmVariable.Simple.Secret.string(name=var_name, value=var_value)
        else:
            variable = CalmVariable.Simple.string(name=var_name, value=var_value)
        variables.append(variable)
    return variables


def http_task(
    method,
    url,
    body=None,
    headers=None,
    secret_headers=None,
    credential=None,
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
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
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
    auth_obj = {"auth_type": "none"}
    if credential is not None:
        if getattr(credential, "__kind__", None) != "app_credential":
            raise ValueError(
                "Credential for HTTP task "
                + (name or "")
                + " should be a Credential object of PASSWORD type"
            )

        # TODO: Auth should be changed to basic auth with credential.
        # This is dependent on https://jira.nutanix.com/browse/CALM-12149
        # We could also possibly check calm server version to switch between
        # the two auth mechanisms since basic auth will be deprecated.
        auth_obj = {
            "auth_type": "basic",
            "basic_auth": {
                "username": credential.username,
                "password": {"value": credential.secret.get("value")},
            },
        }

    kwargs = {
        "name": name,
        "type": "HTTP",
        "attrs": {
            "method": method,
            "url": url,
            "authentication": auth_obj,
            "connection_timeout": timeout,
            "tls_verify": verify,
            "retry_count": retries + 1,
            "retry_interval": retry_interval,
        },
    }

    if body is not None:
        kwargs["attrs"]["request_body"] = body

    if content_type is not None:
        kwargs["attrs"]["content_type"] = content_type

    if target is not None:
        kwargs["target_any_local_reference"] = _get_target_ref(target)

    header_variables = []
    if headers is not None:
        header_variables.extend(_header_variables_from_dict(headers))
        kwargs["attrs"]["headers"] = header_variables

    if secret_headers is not None:
        header_variables.extend(
            _header_variables_from_dict(secret_headers, secret=True)
        )
        kwargs["attrs"]["headers"] = header_variables

    if status_mapping is not None:
        LOG.debug("Status mapping for HTTP Task : {}".format(status_mapping))
        if not isinstance(status_mapping, dict):
            raise TypeError(
                "Status mapping for HTTP task "
                + (name or "")
                + " should be dictionary of int keys and boolean values"
            )
        expected_response = []
        for code, state in status_mapping.items():
            if not isinstance(code, int):
                raise TypeError(
                    "Status mapping for HTTP task "
                    + (name or "")
                    + " should be dictionary of int keys and boolean values"
                )
            if not isinstance(state, bool):
                raise TypeError(
                    "Status mapping for HTTP task "
                    + (name or "")
                    + " should be dictionary of int keys and boolean values"
                )
            expected_response.append(
                {"status": "SUCCESS" if state else "FAILURE", "code": code}
            )
        kwargs["attrs"]["expected_response_params"] = expected_response

    if response_paths is not None:
        LOG.debug("Response paths for HTTP Task : {}".format(response_paths))
        if not isinstance(response_paths, dict):
            raise TypeError(
                "Response paths for HTTP task "
                + (name or "")
                + " should be dictionary of strings"
            )
        for prop, path in response_paths.items():
            if not isinstance(prop, str):
                raise TypeError(
                    "Response paths for HTTP task "
                    + (name or "")
                    + " should be dictionary of strings"
                )
            if not isinstance(path, str):
                raise TypeError(
                    "Response paths for HTTP task "
                    + (name or "")
                    + " should be dictionary of strings"
                )
        kwargs["attrs"]["response_paths"] = response_paths

    return _task_create(**kwargs)


def _deployment_scaling_create(target, scaling_type, scaling_count, name=None):
    if not target:
        raise ValueError("A target is required for deployment scaling task")
    if not isinstance(target, RefType) and isinstance(target, EntityType):
        target = target.get_ref()
    if not target.kind == "app_blueprint_deployment":
        LOG.debug(
            "Target for deployment scaling can be 'app_blueprint_deployment' only"
        )
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
        "attrs": {"scaling_type": scaling_type, "scaling_count": str(scaling_count)},
        "target_any_local_reference": target,
    }

    return _task_create(**kwargs)


def scale_out_task(count, target, name=None):
    """
    Defines a deployment scale out task
    Args:
        count (str): scaling_count
        target (Ref): Target deployment for scale out
        name (str): Name for this task
    Returns:
        (Task): Deployment scale out task
    """
    return _deployment_scaling_create(target, "SCALEOUT", count, name=name)


def scale_in_task(count, target, name=None):
    """
    Defines a deployment scale in task
    Args:
        count (str): scaling_count
        target (Ref): Target deployment for scale in
        name (str): Name for this task
    Returns:
        (Task): Deployment scale in task
    """
    return _deployment_scaling_create(target, "SCALEIN", count, name=name)


def delay_task(delay_seconds=None, name=None, target=None):
    """
    Defines a delay task.
    Args:
        delay_seconds(int): Delay in seconds
        name (str): Name for this task
        target (Ref): Target entity for this task
    Returns:
        (Task): Delay task
    """
    if not isinstance(delay_seconds, int):
        raise TypeError(
            "delay_seconds({}) is expected to be an integer, got {}".format(
                delay_seconds, type(delay_seconds)
            )
        )
    kwargs = {"name": name, "type": "DELAY", "attrs": {"interval_secs": delay_seconds}}
    if target is not None:
        kwargs["target_any_local_reference"] = _get_target_ref(target)
    return _task_create(**kwargs)


class CalmTask:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Exec:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ssh = exec_task_ssh
        powershell = exec_task_powershell
        escript = exec_task_escript

    class HTTP:
        def __new__(
            cls,
            method,
            url,
            body=None,
            headers=None,
            secret_headers=None,
            credential=None,
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
            return http_task(
                method,
                url,
                body=body,
                headers=headers,
                secret_headers=secret_headers,
                credential=credential,
                content_type=content_type,
                timeout=timeout,
                verify=verify,
                retries=retries,
                retry_interval=retry_interval,
                status_mapping=status_mapping,
                response_paths=response_paths,
                name=name,
                target=target,
            )

        get = http_task_get
        post = http_task_post
        put = http_task_put
        delete = http_task_delete

    class SetVariable:
        ssh = set_variable_task_ssh
        powershell = set_variable_task_powershell
        escript = set_variable_task_escript

    class Scaling:
        scale_in = scale_in_task
        scale_out = scale_out_task

    class Delay:
        def __new__(cls, delay_seconds=None, name=None, target=None):
            return delay_task(delay_seconds=delay_seconds, name=name, target=target)
