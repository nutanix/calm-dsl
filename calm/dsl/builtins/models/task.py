import enum
import uuid
import os
import sys
from distutils.version import LooseVersion as LV

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .ref import RefType
from .calm_ref import Ref
from .task_input import TaskInputType
from .variable import CalmVariable
from .helper import common as common_helper
from .utils import is_compile_secrets

from calm.dsl.store.version import Version
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.builtins.models.ndb import (
    DatabaseServer,
    Database,
    TimeMachine,
    PostgresDatabaseOutputVariables,
    Tag,
)
from calm.dsl.builtins.models.constants import NutanixDB as NutanixDBConst
from calm.dsl.constants import CACHE, SUBSTRATE, PROVIDER, TASKS

LOG = get_logging_handle(__name__)

CALM_VERSION = Version.get_version("Calm")


class Status(enum.Enum):

    SUCCESS = 1
    FAILURE = 2
    DONT_CARE = 3


EXIT_CONDITION_MAP = {
    Status.SUCCESS: "on_success",
    Status.FAILURE: "on_failure",
    Status.DONT_CARE: "dont_care",
}


def http_response_code_map(status, code_ranges, code):
    if code:
        if LV(CALM_VERSION) >= LV("3.9.0"):
            if code_ranges:
                response_code_status_map = {
                    "status": status,
                    "code_range_list": code_ranges,
                    "code": code,
                }
            else:
                response_code_status_map = {"status": status, "code": code}
        else:
            response_code_status_map = {"status": status, "code": code}
    else:
        response_code_status_map = {"status": status, "code_range_list": code_ranges}
    return response_code_status_map


class HTTPResponseHandle:
    class TASK_STATUS:
        Success = "SUCCESS"
        Failure = "FAILURE"
        Warning = "WARNING"

    class ResponseCode:
        def __new__(cls, status, code_ranges=[], code=None):
            return http_response_code_map(
                status=status,
                code_ranges=code_ranges,
                code=code,
            )


def task_status_map(result, values):
    task_status_map = {
        "match_values": values,
        "type": StatusHandle.Type.Status,
        "result_status": result,
    }
    return task_status_map


def exit_code_map(result, values):
    exit_code_status_map = {
        "match_values": values,
        "type": StatusHandle.Type.ExitCode,
        "result_status": result,
    }
    return exit_code_status_map


class StatusHandle:
    class Type:
        Status = "status"
        ExitCode = "exit_code"

    class Mapping:
        """
        Exit Code Mapping is allowed for Execute, Set Variable and Decision Task.
        Task Status Mapping is not allowed for Execute Escript task.
        """

        exit_code = exit_code_map
        task_status = task_status_map

    class Result:
        """
        Status can be mapped to only Warning
        """

        Warning = "WARNING"

    class Status:
        """
        TaskFailure can be used for all Exec, Decision and Set Variable Tasks except Escript, VM Operations, HTTP Task.
        Failure can be used only for Loop Task
        """

        TaskFailure = "TASK_FAILURE"
        Failure = "FAILURE"


# Task


class TaskType(EntityType):
    __schema_name__ = "Task"
    __openapi_type__ = "app_task"

    def compile(cls):
        cdict = super().compile()
        if (cdict.get("target_any_local_reference", None) or None) is None:
            cdict.pop("target_any_local_reference", None)
        if (cdict.get("exec_target_reference", None) or None) is None:
            cdict.pop("exec_target_reference", None)
        return cdict

    @classmethod
    def pre_decompile(mcls, cdict, context=[], prefix=""):

        cdict = super().pre_decompile(cdict, context=context, prefix=prefix)
        # Removing additional attributes
        cdict.pop("state", None)
        cdict.pop("message_list", None)

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        return cdict

    @classmethod
    def decompile(mcls, cdict, context=[], prefix=""):

        attrs = cdict.get("attrs", None) or dict()

        cred = attrs.get("login_credential_local_reference", None)
        if cred:
            attrs["login_credential_local_reference"] = RefType.decompile(
                cred, prefix=prefix
            )

        task_type = cdict.get("type", None) or ""

        # If task is of type DAG, decompile references there also
        if task_type == "DAG":
            edges = attrs.get("edges", None) or []
            final_edges = []
            for edge in edges:
                final_edges.append(
                    {
                        "from_task_reference": RefType.decompile(
                            edge["from_task_reference"], prefix=prefix
                        ),
                        "to_task_reference": RefType.decompile(
                            edge["to_task_reference"], prefix=prefix
                        ),
                    }
                )
            if final_edges:
                attrs["edges"] = final_edges

        elif task_type == "CALL_RUNBOOK":
            attrs["runbook_reference"] = RefType.decompile(
                attrs["runbook_reference"], prefix=prefix
            )

        elif task_type == "CALL_CONFIG":
            attrs["config_spec_reference"] = attrs["config_spec_reference"]["name"]

        elif task_type == "HTTP":

            auth_obj = attrs.get("authentication", {})
            auth_type = auth_obj.get("type", "")

            # Note For decompiling, only authentication object of type 'basic_with_cred' works bcz we cann't take secret values at client side
            if auth_type == "basic_with_cred":
                auth_cred = auth_obj.get("credential_local_reference", None)
                if auth_cred:
                    auth_obj["credential_local_reference"] = RefType.decompile(
                        auth_cred, prefix=prefix
                    )

        tunnel_data = attrs.get("tunnel_reference", {})
        if tunnel_data:
            if not tunnel_data.get("name"):
                cache_vpc_data = Cache.get_entity_data_using_uuid(
                    CACHE.ENTITY.AHV_VPC, None, tunnel_uuid=tunnel_data["uuid"]
                )

                # Decompile should not fail
                if not cache_vpc_data:
                    LOG.info(
                        "tunnel(uuid={}) used in task (name={}) not found".format(
                            tunnel_data["uuid"], cdict["name"]
                        )
                    )
                    attrs.pop("tunnel_reference", None)

                else:
                    tunnel_data["name"] = cache_vpc_data.get("tunnel_name")

        cdict["attrs"] = attrs

        return super().decompile(cdict, context=context, prefix=prefix)


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

        if main_dag.target_any_local_reference.kind != "app_service":
            LOG.error("Runbook Tasks are only allowed for service actions")
            sys.exit(-1)

    return _task_create(**kwargs)


def create_call_config(target, config, name):
    kwargs = {
        "name": name
        or "Call_Config_task_for_{}__{}".format(target.name, str(uuid.uuid4())[:8]),
        "type": "CALL_CONFIG",
        "attrs": {"config_spec_reference": _get_target_ref(config)},
    }
    kwargs["target_any_local_reference"] = _get_target_ref(target)
    return _task_create(**kwargs)


def _exec_create(
    script_type,
    script=None,
    filename=None,
    name=None,
    target=None,
    target_endpoint=None,
    cred=None,
    depth=2,
    tunnel=None,
    status_map_list=[],
    **kwargs,
):
    if script is not None and filename is not None:
        raise ValueError(
            "Only one of script or filename should be given for exec task "
            + (name or "")
        )
    cls_type = kwargs.get("cls_type", None)
    if (
        not (cls_type and issubclass(cls_type, ProviderTask))
        and script_type not in ["static", "static_py3"]
        and tunnel is not None
    ):
        raise ValueError("Tunnel is supported only for Escript script types")

    if filename is not None:
        if cls_type and issubclass(cls_type, ProviderTask):
            depth += 1
        file_path = os.path.join(
            os.path.dirname(sys._getframe(depth).f_globals.get("__file__")), filename
        )
        with open(file_path, "r") as scriptf:
            script = scriptf.read()

    if script is None:
        raise ValueError(
            "One of script or filename is required for exec task " + (name or "")
        )
    params = {
        "name": name,
        "type": "EXEC",
        "attrs": {"script_type": script_type, "script": script},
    }
    if LV(CALM_VERSION) >= LV("3.9.0"):
        params["status_map_list"] = status_map_list
    if cred is not None:
        params["attrs"]["login_credential_local_reference"] = _get_target_ref(cred)
    if target is not None:
        params["target_any_local_reference"] = _get_target_ref(target)
    if target_endpoint is not None:
        params["exec_target_reference"] = _get_target_ref(target_endpoint)
    if tunnel is not None:
        params["attrs"]["tunnel_reference"] = tunnel
    if "inherit_target" in kwargs:
        params["inherit_target"] = kwargs.get("inherit_target")
    if kwargs.get("ip"):
        params["attrs"]["ip"] = kwargs["ip"]
    if kwargs.get("port"):
        params["attrs"]["port"] = kwargs["port"]
    if kwargs.get("connection_protocol"):
        params["attrs"]["connection_protocol"] = kwargs["connection_protocol"]
    return _task_create(**params)


def _decision_create(
    script_type,
    script=None,
    filename=None,
    name=None,
    target=None,
    cred=None,
    depth=2,
    tunnel=None,
    status_map_list=[],
    **kwargs,
):
    if script is not None and filename is not None:
        raise ValueError(
            "Only one of script or filename should be given for decision task "
            + (name or "")
        )

    cls_type = kwargs.get("cls_type", None)
    if filename is not None:
        if cls_type and issubclass(cls_type, ProviderTask):
            depth += 1
        file_path = os.path.join(
            os.path.dirname(sys._getframe(depth).f_globals.get("__file__")), filename
        )

        with open(file_path, "r") as scriptf:
            script = scriptf.read()

    if script is None:
        raise ValueError(
            "One of script or filename is required for decision task " + (name or "")
        )

    if (
        not (cls_type and issubclass(cls_type, ProviderTask))
        and script_type not in ["static", "static_py3"]
        and tunnel is not None
    ):
        raise ValueError("Tunnel is support only for Escript script types")

    params = {
        "name": name,
        "type": "DECISION",
        "attrs": {
            "script_type": script_type,
            "script": script,
        },
    }
    if LV(CALM_VERSION) >= LV("3.9.0"):
        params["status_map_list"] = status_map_list
    if cred is not None:
        params["attrs"]["login_credential_local_reference"] = _get_target_ref(cred)
    if target is not None:
        params["target_any_local_reference"] = _get_target_ref(target)
    if tunnel is not None:
        params["attrs"]["tunnel_reference"] = tunnel
    if "inherit_target" in kwargs:
        params["inherit_target"] = kwargs.get("inherit_target")
    if kwargs.get("ip"):
        params["attrs"]["ip"] = kwargs["ip"]
    if kwargs.get("port"):
        params["attrs"]["port"] = kwargs["port"]
    if kwargs.get("connection_protocol"):
        params["attrs"]["connection_protocol"] = kwargs["connection_protocol"]
    return _task_create(**params)


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


def parallel_task(name=None, child_tasks=[], attrs={}):
    """
    Create a PARALLEL task
    Args:
        name (str): Name for the task
        child_tasks (list [Task]): Child tasks within this dag
        attrs (dict): Task's attrs
    Returns:
        (Task): PARALLEL task
    """

    # This follows UI naming convention for runbooks
    name = name or str(uuid.uuid4())[:8] + "_parallel"
    kwargs = {
        "name": name,
        "child_tasks_local_reference_list": [
            task.get_ref() for task in child_tasks or []
        ],
        "type": "PARALLEL",
    }

    return _task_create(**kwargs)


def while_loop(name=None, child_tasks=[], attrs={}, status_map_list=[], **kwargs):
    """
    Create a WHILE LOOP
    Args:
        name (str): Name for the task
        child_tasks (list [Task]): Child tasks within this dag
        attrs (dict): Task's attrs
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        (Task): WHILE task
    """

    # This follows UI naming convention for runbooks
    name = name or str(uuid.uuid4())[:8] + "_while_loop"
    params = {
        "name": name,
        "child_tasks_local_reference_list": [
            task.get_ref() for task in child_tasks or []
        ],
        "type": "WHILE_LOOP",
        "attrs": attrs,
    }
    if LV(CALM_VERSION) >= LV("3.9.0"):
        params["status_map_list"] = status_map_list
    if "inherit_target" in kwargs:
        params["inherit_target"] = kwargs.get("inherit_target")
    return _task_create(**params)


def meta(name=None, child_tasks=None, edges=None, target=None):
    """
    Create a META task
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
    # This follows UI naming convention for runbooks
    name = name or str(uuid.uuid4())[:8] + "_meta"
    kwargs = {
        "name": name,
        "child_tasks_local_reference_list": [
            task.get_ref() for task in child_tasks or []
        ],
        "type": "META",
    }
    if target:
        kwargs["target_any_local_reference"] = target

    return _task_create(**kwargs)


def vm_power_action_task(name=None, action_name=None, provider=None, target=None):
    """
    Create a VM POWER ON/OFF/RESTART task
    Args:
        name (str): Name for the task
        provider (str): Type of provider
        action_name (str): Valid power action name
        target (Ref): Target entity reference
    Returns:
        (Task): DAG task
    """
    if action_name not in list(SUBSTRATE.VM_POWER_ACTIONS_REV.keys()):
        LOG.error(
            "{} is not a valid vm power on action {}".format(
                list(SUBSTRATE.VM_POWER_ACTIONS_REV.keys())
            )
        )
        sys.exit(-1)

    # name follows UI naming convention for runbooks
    kwargs = {
        "name": name
        or "SYS_GEN__{}_Operation_{}_".format(
            PROVIDER.NAME[provider], SUBSTRATE.POWER_ACTION_CAMEL_CASE[action_name]
        )
        + str(uuid.uuid4())[:8],
        "type": TASKS.TASK_TYPES.VM_OPERATION[provider],
        "attrs": {
            "operation_type": action_name,
            "type": TASKS.TASK_TYPES.GENERIC_OPERATION,
        },
    }

    if target:
        kwargs["target_any_local_reference"] = _get_target_ref(target)

    return _task_create(**kwargs)


def check_login(name=None, readiness_probe=None, target=None):
    """
    Create a VM CHECK LOGIN task.
    Args:
        name (str): Name for the task
        readiness_probe (dict): Compiled readiness probe data
        target (Ref): Target entity reference
    Returns:
        (Task): DAG task
    """

    if not target:
        LOG.error("Target not supplied")
    if not readiness_probe:
        LOG.error("Readiness probe not supplied")

    substrate_name = "Substrate"  # Default substrate name
    if isinstance(target, EntityType):
        substrate_name = target.name or target.__name__
    elif isinstance(target, RefType):
        substrate_name = target.__self__.name or target.__self__.__name__
    else:
        raise ValueError("Target is not of ref or entity type")

    # This follows UI naming convention for runbooks
    name = (
        name
        or "SYS_GEN__check_login_for_" + substrate_name + "_" + str(uuid.uuid4())[:8]
    )
    kwargs = {
        "name": name,
        "type": TASKS.TASK_TYPES.CHECK_LOGIN,
        "attrs": {
            "retries": readiness_probe["retries"],
            "dial_timeout": "",
            "timeout": readiness_probe["delay_secs"],
            "address": readiness_probe["address"],
            "type": TASKS.TASK_TYPES.CHECK_LOGIN,
            "sleep_time": "",
        },
    }

    kwargs["target_any_local_reference"] = _get_target_ref(target)

    return _task_create(**kwargs)


def exec_task_ssh(
    script=None,
    filename=None,
    name=None,
    target=None,
    target_endpoint=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    return _exec_create(
        "sh",
        script=script,
        filename=filename,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def exec_task_escript(
    script=None,
    filename=None,
    name=None,
    target=None,
    depth=2,
    tunnel=None,
    status_map_list=[],
    **kwargs,
):
    return _exec_create(
        "static",
        script=script,
        filename=filename,
        name=name,
        target=target,
        target_endpoint=None,
        depth=depth,
        tunnel=tunnel,
        status_map_list=status_map_list,
        **kwargs,
    )


def exec_task_escript_py3(
    script=None,
    filename=None,
    name=None,
    target=None,
    depth=2,
    tunnel=None,
    status_map_list=[],
    **kwargs,
):
    return _exec_create(
        "static_py3",
        script=script,
        filename=filename,
        name=name,
        target=target,
        target_endpoint=None,
        depth=depth,
        tunnel=tunnel,
        status_map_list=status_map_list,
        **kwargs,
    )


def exec_task_powershell(
    script=None,
    filename=None,
    name=None,
    target=None,
    target_endpoint=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    return _exec_create(
        "npsscript",
        script=script,
        filename=filename,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def exec_task_python(
    script=None,
    filename=None,
    name=None,
    target=None,
    target_endpoint=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    return _exec_create(
        "python_remote",
        script=script,
        filename=filename,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def exec_task_ssh_runbook(
    script=None,
    filename=None,
    name=None,
    target=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create exec task with shell target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Exec task object
    """
    return _exec_create(
        "sh",
        script=script,
        filename=filename,
        name=name,
        target=target,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def exec_task_powershell_runbook(
    script=None,
    filename=None,
    name=None,
    target=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create exec task with shell target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Exec task object
    """
    return _exec_create(
        "npsscript",
        script=script,
        filename=filename,
        name=name,
        target=target,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def exec_task_python_runbook(
    script=None,
    filename=None,
    name=None,
    target=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create exec task with python_remote target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Exec task object
    """
    return _exec_create(
        "python_remote",
        script=script,
        filename=filename,
        name=name,
        target=target,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def decision_task_ssh(
    script=None,
    filename=None,
    name=None,
    target=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create decision task with shell target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Decision task object
    """
    return _decision_create(
        "sh",
        script=script,
        filename=filename,
        name=name,
        target=target,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def decision_task_powershell(
    script=None,
    filename=None,
    name=None,
    target=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create decision task with powershell target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Decision task object
    """
    return _decision_create(
        "npsscript",
        script=script,
        filename=filename,
        name=name,
        target=target,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def decision_task_python(
    script=None,
    filename=None,
    name=None,
    target=None,
    cred=None,
    depth=2,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create decision task with python_remote target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Decision task object
    """
    return _decision_create(
        "python_remote",
        script=script,
        filename=filename,
        name=name,
        target=target,
        cred=cred,
        depth=depth,
        status_map_list=status_map_list,
        **kwargs,
    )


def decision_task_escript(
    script=None,
    filename=None,
    name=None,
    target=None,
    depth=2,
    tunnel=None,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create decision task with escript target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        tunnel (ref.Tunnel): Tunnel reference
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Decision task object
    """
    return _decision_create(
        "static",
        script=script,
        filename=filename,
        name=name,
        target=target,
        depth=depth,
        tunnel=tunnel,
        status_map_list=status_map_list,
        **kwargs,
    )


def decision_task_escript_py3(
    script=None,
    filename=None,
    name=None,
    target=None,
    depth=2,
    tunnel=None,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create decision task with escript(python3) target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        tunnel (ref.Tunnel): Tunnel reference
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Decision task object
    """
    return _decision_create(
        "static_py3",
        script=script,
        filename=filename,
        name=name,
        target=target,
        depth=depth,
        tunnel=tunnel,
        status_map_list=status_map_list,
        **kwargs,
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
    target_endpoint=None,
    variables=None,
    depth=3,
    cred=None,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create set variable task with shell target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Set variable task object
    """
    task = exec_task_ssh(
        script=script,
        filename=filename,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        depth=depth,
        cred=cred,
        status_map_list=status_map_list,
        **kwargs,
    )
    return _set_variable_create(task, variables)


def set_variable_task_escript(
    script=None,
    filename=None,
    name=None,
    target=None,
    variables=None,
    depth=3,
    tunnel=None,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create set variable task with escript target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        tunnel (Ref.Tunnel): Tunnel reference
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Set variable task object
    """
    task = exec_task_escript(
        script=script,
        filename=filename,
        name=name,
        target=target,
        depth=depth,
        tunnel=tunnel,
        status_map_list=status_map_list,
        **kwargs,
    )
    return _set_variable_create(task, variables)


def set_variable_task_escript_py3(
    script=None,
    filename=None,
    name=None,
    target=None,
    variables=None,
    depth=3,
    tunnel=None,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create set variable task with escript(python3) target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        tunnel (Ref.Tunnel): Tunnel reference
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Set variable task object
    """
    task = exec_task_escript_py3(
        script=script,
        filename=filename,
        name=name,
        target=target,
        depth=depth,
        tunnel=tunnel,
        status_map_list=status_map_list,
        **kwargs,
    )
    return _set_variable_create(task, variables)


def set_variable_task_powershell(
    script=None,
    filename=None,
    name=None,
    target=None,
    target_endpoint=None,
    variables=None,
    depth=3,
    cred=None,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create set variable task with powershell target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Set variable task object
    """
    task = exec_task_powershell(
        script=script,
        filename=filename,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        depth=depth,
        cred=cred,
        status_map_list=status_map_list,
        **kwargs,
    )
    return _set_variable_create(task, variables)


def set_variable_task_python(
    script=None,
    filename=None,
    name=None,
    target=None,
    target_endpoint=None,
    variables=None,
    depth=3,
    cred=None,
    status_map_list=[],
    **kwargs,
):
    """
    This function is used to create set variable task with python_remote target
    Args:
        script(str): Script which needs to be run
        filename(str): file which has script
        name(str): Task name
        target(Entity/Ref): Entity/Ref that is the target for this task
        cred (Entity/Ref): Entity/Ref that is the cred for this task
        depth (int): Number of times to look back in call stack, will be used to locate filename specified
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        obj: Set variable task object
    """
    task = exec_task_python(
        script=script,
        filename=filename,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        depth=depth,
        cred=cred,
        status_map_list=status_map_list,
        **kwargs,
    )
    return _set_variable_create(task, variables)


class EscriptTaskType:
    class ExecTask:
        def __new__(
            cls,
            script=None,
            filename=None,
            name=None,
            target=None,
            depth=2,
            tunnel=None,
            status_map_list=[],
            **kwargs,
        ):
            return exec_task_escript_py3(
                script=script,
                filename=filename,
                name=name,
                target=target,
                depth=depth + 1,
                tunnel=tunnel,
                status_map_list=status_map_list,
                **kwargs,
            )

        py2 = exec_task_escript
        py3 = exec_task_escript_py3

    class DecisionTask:
        def __new__(
            cls,
            script=None,
            filename=None,
            name=None,
            target=None,
            depth=2,
            tunnel=None,
            status_map_list=[],
            **kwargs,
        ):
            return decision_task_escript_py3(
                script=script,
                filename=filename,
                name=name,
                target=target,
                depth=depth + 1,
                tunnel=tunnel,
                status_map_list=status_map_list,
                **kwargs,
            )

        py2 = decision_task_escript
        py3 = decision_task_escript_py3

    class SetVariableTask:
        def __new__(
            cls,
            script=None,
            filename=None,
            name=None,
            target=None,
            variables=None,
            depth=3,
            tunnel=None,
            status_map_list=[],
            **kwargs,
        ):
            return set_variable_task_escript_py3(
                script=script,
                filename=filename,
                name=name,
                target=target,
                variables=variables,
                depth=depth + 1,
                tunnel=tunnel,
                status_map_list=status_map_list,
                **kwargs,
            )

        py2 = set_variable_task_escript
        py3 = set_variable_task_escript_py3


def http_task_on_endpoint(
    method,
    relative_url=None,
    body=None,
    headers=None,
    secret_headers=None,
    content_type=None,
    status_mapping=None,
    response_code_status_map=[],
    response_paths=None,
    name=None,
    target=None,
    status_map_list=[],
    **kwargs,
):
    """

    Defines a HTTP Task on http endpoint target.

    Args:
        method (str): HTTP method ("GET", "POST", "PUT", "DELETE", ..)
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        content_type (string): Request Content-Type (application/json, application/xml, etc.)
        status_mapping (dict): Mapping of  Response status code (int) to
                               task status (True: success, False: Failure)
        response_code_status_map (list): List of Response code ranges mapping
        response_paths (dict): Mapping of variable name (str) to path in response (str)
        name (str): Task name
        target (Ref): Target entity that this task runs under.
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        (Task): HTTP Task
    """
    return http_task(
        method,
        "",  # As url is present is target endpoint
        body=body,
        relative_url=relative_url,
        headers=headers,
        secret_headers=secret_headers,
        content_type=content_type,
        status_mapping=status_mapping,
        response_code_status_map=response_code_status_map,
        response_paths=response_paths,
        name=name,
        target=target,
        status_map_list=status_map_list,
        **kwargs,
    )


def http_task_get_on_endpoint(**kwargs):
    """

    Defines a HTTP GET Task on http endpoint target.

    Args:
        kwargs (Ref): keyword arguments for http task on endpoint
    Returns:
        (Task): HTTP Task
    """
    return http_task_on_endpoint("GET", **kwargs)


def http_task_post_on_endpoint(**kwargs):
    """

    Defines a HTTP POST Task on http endpoint target.

    Args:
        kwargs (Ref): keyword arguments for http task on endpoint
    Returns:
        (Task): HTTP Task
    """
    return http_task_on_endpoint("POST", **kwargs)


def http_task_put_on_endpoint(**kwargs):
    """

    Defines a HTTP PUT Task on http endpoint target.

    Args:
        kwargs (Ref): keyword arguments for http task on endpoint
    Returns:
        (Task): HTTP Task
    """
    return http_task_on_endpoint("PUT", **kwargs)


def http_task_delete_on_endpoint(**kwargs):
    """

    Defines a HTTP GET Task on http endpoint target.

    Args:
        kwargs (Ref): keyword arguments for http task on endpoint
    Returns:
        (Task): HTTP Task
    """
    return http_task_on_endpoint("DELETE", **kwargs)


def http_task_get(
    url="",
    relative_url=None,
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
    response_code_status_map=[],
    response_paths=None,
    name=None,
    target=None,
    target_endpoint=None,
    cred=None,
    tunnel=None,
    status_map_list=[],
):
    """

    Defines a HTTP GET Task.

    Args:
        url (str): Request URL (https://example.com/dummy_url)
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
        cred (Credential reference): Used for basic_with_cred authentication
        content_type (string): Request Content-Type (application/json, application/xml, etc.)
        timeout (int): Request timeout in seconds (Default: 120)
        verify (bool): TLS verify (Default: False)
        retries (int): Number of times to retry this request if it fails. (Default: 0)
        retry_interval (int): Time to wait in seconds between retries (Default: 10)
        status_mapping (dict): Mapping of  Response status code (int) to
                               task status (True: success, False: Failure)
        response_code_status_map (list): List of Response code ranges mapping
        response_paths (dict): Mapping of variable name (str) to path in response (str)
        name (str): Task name
        target (Ref): Target entity that this task runs under.
        tunnel (Ref.Tunnel): Tunnel reference
    Returns:
        (Task): HTTP Task
    """
    return http_task(
        "GET",
        url,
        relative_url=relative_url,
        body=None,
        headers=headers,
        secret_headers=secret_headers,
        credential=credential,
        cred=cred,
        content_type=content_type,
        timeout=timeout,
        verify=verify,
        retries=retries,
        retry_interval=retry_interval,
        status_mapping=status_mapping,
        response_code_status_map=response_code_status_map,
        response_paths=response_paths,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        tunnel=tunnel,
        status_map_list=status_map_list,
    )


def http_task_post(
    url="",
    relative_url=None,
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
    response_code_status_map=[],
    response_paths=None,
    name=None,
    target=None,
    target_endpoint=None,
    cred=None,
    tunnel=None,
    status_map_list=[],
):
    """

    Defines a HTTP POST Task.

    Args:
        url (str): Request URL (https://example.com/dummy_url)
        body (str): Request body
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
        cred (Credential reference): Used for basic_with_cred authentication
        content_type (string): Request Content-Type (application/json, application/xml, etc.)
        timeout (int): Request timeout in seconds (Default: 120)
        verify (bool): TLS verify (Default: False)
        retries (int): Number of times to retry this request if it fails. (Default: 0)
        retry_interval (int): Time to wait in seconds between retries (Default: 10)
        status_mapping (dict): Mapping of  Response status code (int) to
                               task status (True: success, False: Failure)
        response_code_status_map (list): List of Response code ranges mapping
        response_paths (dict): Mapping of variable name (str) to path in response (str)
        name (str): Task name
        target (Ref): Target entity that this task runs under.
        tunnel (Ref.Tunnel): Tunnel reference
    Returns:
        (Task): HTTP Task
    """
    return http_task(
        "POST",
        url,
        relative_url=relative_url,
        body=body,
        headers=headers,
        secret_headers=secret_headers,
        credential=credential,
        cred=cred,
        content_type=content_type,
        timeout=timeout,
        verify=verify,
        retries=retries,
        retry_interval=retry_interval,
        status_mapping=status_mapping,
        response_code_status_map=response_code_status_map,
        response_paths=response_paths,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        tunnel=tunnel,
        status_map_list=status_map_list,
    )


def http_task_put(
    url="",
    relative_url=None,
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
    response_code_status_map=[],
    response_paths=None,
    name=None,
    target=None,
    target_endpoint=None,
    cred=None,
    tunnel=None,
    status_map_list=[],
):
    """

    Defines a HTTP PUT Task.

    Args:
        url (str): Request URL (https://example.com/dummy_url)
        body (str): Request body
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
        cred (Credential reference): Used for basic_with_cred authentication
        content_type (string): Request Content-Type (application/json, application/xml, etc.)
        timeout (int): Request timeout in seconds (Default: 120)
        verify (bool): TLS verify (Default: False)
        retries (int): Number of times to retry this request if it fails. (Default: 0)
        retry_interval (int): Time to wait in seconds between retries (Default: 10)
        status_mapping (dict): Mapping of  Response status code (int) to
                               task status (True: success, False: Failure)
        response_code_status_map (list): List of Response code ranges mapping
        response_paths (dict): Mapping of variable name (str) to path in response (str)
        name (str): Task name
        target (Ref): Target entity that this task runs under.
        tunnel (Ref.Tunnel): Tunnel reference
    Returns:
        (Task): HTTP Task
    """
    return http_task(
        "PUT",
        url,
        relative_url=relative_url,
        body=body,
        headers=headers,
        secret_headers=secret_headers,
        credential=credential,
        cred=cred,
        content_type=content_type,
        timeout=timeout,
        verify=verify,
        retries=retries,
        retry_interval=retry_interval,
        status_mapping=status_mapping,
        response_code_status_map=response_code_status_map,
        response_paths=response_paths,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        tunnel=tunnel,
        status_map_list=status_map_list,
    )


def http_task_delete(
    url="",
    relative_url=None,
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
    response_code_status_map=[],
    response_paths=None,
    name=None,
    target=None,
    target_endpoint=None,
    cred=None,
    tunnel=None,
    status_map_list=[],
):
    """

    Defines a HTTP DELETE Task.

    Args:
        url (str): Request URL (https://example.com/dummy_url)
        body (str): Request body
        headers (dict): Request headers
        secret_headers (dict): Request headers that are to be masked
        credential (Credential): Credential object. Currently only supports basic auth.
        cred (Credential reference): Used for basic_with_cred authentication
        content_type (string): Request Content-Type (application/json, application/xml, etc.)
        timeout (int): Request timeout in seconds (Default: 120)
        verify (bool): TLS verify (Default: False)
        retries (int): Number of times to retry this request if it fails. (Default: 0)
        retry_interval (int): Time to wait in seconds between retries (Default: 10)
        status_mapping (dict): Mapping of  Response status code (int) to
                               task status (True: success, False: Failure)
        response_code_status_map (list): List of Response code ranges mapping
        response_paths (dict): Mapping of variable name (str) to path in response (str)
        name (str): Task name
        target (Ref): Target entity that this task runs under.
        tunnel (Ref.Tunnel): Tunnel Reference
    Returns:
        (Task): HTTP Task
    """
    return http_task(
        "DELETE",
        url,
        relative_url=relative_url,
        body=body,
        headers=headers,
        secret_headers=secret_headers,
        credential=credential,
        cred=cred,
        content_type=content_type,
        timeout=timeout,
        verify=verify,
        retries=retries,
        retry_interval=retry_interval,
        status_mapping=status_mapping,
        response_code_status_map=response_code_status_map,
        response_paths=response_paths,
        name=name,
        target=target,
        target_endpoint=target_endpoint,
        tunnel=tunnel,
        status_map_list=status_map_list,
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
    relative_url=None,
    body=None,
    headers=None,
    secret_headers=None,
    credential=None,
    cred=None,
    content_type=None,
    timeout=120,
    verify=False,
    retries=0,
    retry_interval=10,
    status_mapping=None,
    response_code_status_map=[],
    response_paths=None,
    name=None,
    target=None,
    target_endpoint=None,
    tunnel=None,
    status_map_list=[],
    **kwargs,
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
        cred (Credential reference): Used for basic_with_cred authentication
        content_type (string): Request Content-Type (application/json, application/xml, etc.)
        timeout (int): Request timeout in seconds (Default: 120)
        verify (bool): TLS verify (Default: False)
        retries (int): Number of times to retry this request if it fails. (Default: 0)
        retry_interval (int): Time to wait in seconds between retries (Default: 10)
        status_mapping (dict): Mapping of  Response status code (int) to
                               task status (True: success, False: Failure)
        response_code_status_map (list): List of Response code ranges mapping
        response_paths (dict): Mapping of variable name (str) to path in response (str)
        name (str): Task name
        target (Ref): Target entity that this task runs under.
        tunnel (Ref.Tunnel): Tunnel reference
    Returns:
        (Task): HTTP Task
    """
    auth_obj = {"auth_type": "none"}

    # Auth object for basic auth with credential.
    if cred is not None:
        cred_ref = _get_target_ref(cred)
        if getattr(cred_ref, "kind", None) != "app_credential":
            raise ValueError(
                "Cred for HTTP task "
                + (name or "")
                + " should be reference of credential object"
            )

        auth_obj = {
            "type": "basic_with_cred",
            "credential_local_reference": cred_ref,
        }

    # Auth object for basic auth
    elif credential is not None:
        if getattr(credential, "__kind__", None) != "app_credential":
            raise ValueError(
                "Credential for HTTP task "
                + (name or "")
                + " should be a Credential object of PASSWORD type"
            )

        auth_obj = {
            "auth_type": "basic",
            "basic_auth": {
                "username": credential.username,
                "password": {
                    "value": credential.secret.get("value")
                    if is_compile_secrets()
                    else "",
                    "attrs": {"is_secret_modified": True},
                },
            },
        }

    params = {
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

    if LV(CALM_VERSION) >= LV("3.9.0"):
        params["status_map_list"] = status_map_list

    if relative_url is not None:
        params["attrs"]["relative_url"] = relative_url

    if body is not None:
        params["attrs"]["request_body"] = body

    if content_type is not None:
        params["attrs"]["content_type"] = content_type

    if target is not None:
        params["target_any_local_reference"] = _get_target_ref(target)

    if target_endpoint is not None:
        params["exec_target_reference"] = _get_target_ref(target_endpoint)

    header_variables = []
    if headers is not None:
        header_variables.extend(_header_variables_from_dict(headers))
        params["attrs"]["headers"] = header_variables

    if secret_headers is not None:
        header_variables.extend(
            _header_variables_from_dict(secret_headers, secret=True)
        )
        params["attrs"]["headers"] = header_variables

    # If both response code status map and status mapping is present raise the error
    if status_mapping and response_code_status_map:
        err_msg = "Both status_mapping and response_code_status_map cannot be present together. status_mapping is now deprecated, start using response_code_status_map"
        LOG.error(err_msg)
        sys.exit(-1)

    if status_mapping is not None:
        LOG.warning(
            "status_mapping will be deprecated soon, start using response_code_status_map"
        )
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
        params["attrs"]["expected_response_params"] = expected_response

    if response_code_status_map:
        params["attrs"]["expected_response_params"] = response_code_status_map

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
        params["attrs"]["response_paths"] = response_paths

    if "inherit_target" in kwargs:
        params["inherit_target"] = kwargs.get("inherit_target")

    if tunnel is not None:
        params["attrs"]["tunnel_reference"] = tunnel

    return _task_create(**params)


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


def vm_operation(
    name=None, type="VM_OPERATION", target=None, status_map_list=[], **kwargs
):
    """
    Defines a vm_operation task i.e. POWERON/ POWEROFF/ RESTART
    Args:
        name (str): Name for this task
        type(str): Task Type
        target (Ref): Target entity for this task
        :keyword inherit_target (bool): True if target needs to be inherited.
    Returns:
        (Task): VM Operation task
    """
    params = {"name": name, "type": type}
    if LV(CALM_VERSION) >= LV("3.9.0"):
        params["status_map_list"] = status_map_list

    if target is not None:
        params["target_any_local_reference"] = _get_target_ref(target)
    if "inherit_target" in kwargs:
        params["inherit_target"] = kwargs.get("inherit_target")
    return _task_create(**params)


def input_task(timeout=None, name=None, inputs=[]):
    """
    Defines a input task.
    Args:
        timeout(int): Task timeout in seconds
        name (str): Name for this task
        inputs (list): list of inputs for the task
    Returns:
        (Task): Delay task
    """
    if not isinstance(timeout, int):
        raise TypeError(
            "timeout is expected to be an integer, got {}".format(type(timeout))
        )
    kwargs = {
        "name": name,
        "type": "INPUT",
        "attrs": {"task_timeout": timeout, "inputs": []},
    }
    for task_input in inputs:
        if not isinstance(task_input, TaskInputType):
            raise TypeError(
                "All inputs is expected to be an TaskInputType, got {}".format(
                    type(task_input)
                )
            )
        kwargs["attrs"]["inputs"].append(
            {
                "name": task_input.name,
                "input_type": task_input.input_type,
                "options": task_input.options,
            }
        )
    return _task_create(**kwargs)


def confirm_task(timeout=None, name=None):
    """
    Defines a confirm task.
    Args:
        timeout(int): Task timeout in seconds
        name (str): Name for this task
    Returns:
        (Task): Delay task
    """
    if not isinstance(timeout, int):
        raise TypeError(
            "timeout is expected to be an integer, got {}".format(type(timeout))
        )
    kwargs = {"name": name, "type": "CONFIRM", "attrs": {"task_timeout": timeout}}
    return _task_create(**kwargs)


def resource_type_operation_task_builder(
    name,
    resource_type_ref,
    action_ref,
    account_ref=None,
    inarg_list=[],
    target_ref=None,
    output_variables=None,
    tag=None,
):
    kwargs = {
        "name": name,
        "type": "RT_OPERATION",
        "attrs": {
            "type": "RT_OPERATION",
            "resource_type_reference": resource_type_ref,
            "action_reference": action_ref,
            "inarg_list": inarg_list,
            "output_variables": output_variables,
            "tag": tag,
        },
    }
    if target_ref:
        kwargs["target_any_local_reference"] = target_ref

    if account_ref:
        kwargs["attrs"]["account_reference"] = account_ref
    return _task_create(**kwargs)


class BaseTask:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class HTTP:
        def __new__(
            cls,
            method,
            url="",
            relative_url=None,
            body=None,
            headers=None,
            secret_headers=None,
            credential=None,
            cred=None,
            content_type=None,
            timeout=120,
            verify=False,
            retries=0,
            retry_interval=10,
            status_mapping=None,
            response_code_status_map=[],
            response_paths=None,
            name=None,
            target=None,
            target_endpoint=None,
            tunnel=None,
            status_map_list=[],
        ):
            return http_task(
                method,
                url,
                relative_url,
                body=body,
                headers=headers,
                secret_headers=secret_headers,
                credential=credential,
                cred=cred,
                content_type=content_type,
                timeout=timeout,
                verify=verify,
                retries=retries,
                retry_interval=retry_interval,
                status_mapping=status_mapping,
                response_code_status_map=response_code_status_map,
                response_paths=response_paths,
                name=name,
                target=target,
                target_endpoint=target_endpoint,
                tunnel=tunnel,
                status_map_list=status_map_list,
            )

        get = http_task_get
        post = http_task_post
        put = http_task_put
        delete = http_task_delete

    class SetVariable:
        ssh = set_variable_task_ssh
        powershell = set_variable_task_powershell
        escript = EscriptTaskType.SetVariableTask
        python = set_variable_task_python

    class Delay:
        def __new__(cls, delay_seconds=None, name=None, target=None):
            return delay_task(delay_seconds=delay_seconds, name=name, target=target)


class CalmTask(BaseTask):
    class Scaling:
        scale_in = scale_in_task
        scale_out = scale_out_task

    class Exec:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ssh = exec_task_ssh
        powershell = exec_task_powershell
        escript = EscriptTaskType.ExecTask
        python = exec_task_python

    class ConfigExec:
        def __new__(cls, config, name=None):
            target = config.__self__.attrs_list[0]["target_any_local_reference"]
            if not target:
                raise Exception(
                    "Config's target has to be specified for it be used in ConfigExec Task"
                )
            return create_call_config(target, config, name)


class ProviderTask(CalmTask):
    class Exec:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ssh = lambda **kwargs: exec_task_ssh(cls_type=ProviderTask, **kwargs)
        powershell = lambda **kwargs: exec_task_powershell(
            cls_type=ProviderTask, **kwargs
        )
        escript = lambda **kwargs: EscriptTaskType.ExecTask(
            cls_type=ProviderTask, **kwargs
        )
        escript.py2 = lambda **kwargs: EscriptTaskType.ExecTask.py2(
            cls_type=ProviderTask, **kwargs
        )
        escript.py3 = lambda **kwargs: EscriptTaskType.ExecTask.py3(
            cls_type=ProviderTask, **kwargs
        )
        python = lambda **kwargs: exec_task_python(cls_type=ProviderTask, **kwargs)

    class SetVariable:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ssh = lambda **kwargs: set_variable_task_ssh(cls_type=ProviderTask, **kwargs)
        powershell = lambda **kwargs: set_variable_task_powershell(
            cls_type=ProviderTask, **kwargs
        )
        escript = lambda **kwargs: EscriptTaskType.SetVariableTask(
            cls_type=ProviderTask, **kwargs
        )
        escript.py2 = lambda **kwargs: EscriptTaskType.SetVariableTask.py2(
            cls_type=ProviderTask, **kwargs
        )
        escript.py3 = lambda **kwargs: EscriptTaskType.SetVariableTask.py3(
            cls_type=ProviderTask, **kwargs
        )
        python = lambda **kwargs: set_variable_task_python(
            cls_type=ProviderTask, **kwargs
        )

    class Decision:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ssh = lambda **kwargs: decision_task_ssh(cls_type=ProviderTask, **kwargs)
        powershell = lambda **kwargs: decision_task_powershell(
            cls_type=ProviderTask, **kwargs
        )
        escript = lambda **kwargs: EscriptTaskType.DecisionTask(
            cls_type=ProviderTask, **kwargs
        )
        escript.py2 = lambda **kwargs: EscriptTaskType.DecisionTask.py2(
            cls_type=ProviderTask, **kwargs
        )
        escript.py3 = lambda **kwargs: EscriptTaskType.DecisionTask.py3(
            cls_type=ProviderTask, **kwargs
        )
        python = lambda **kwargs: decision_task_python(cls_type=ProviderTask, **kwargs)

    class Loop:
        def __new__(
            cls,
            iterations,
            name=None,
            child_tasks=[],
            loop_variable="iteration",
            exit_condition=Status.DONT_CARE,
            **kwargs,
        ):
            attrs = {"iterations": str(iterations), "loop_variable": loop_variable}
            exit_code = EXIT_CONDITION_MAP.get(exit_condition, None)
            if exit_code:
                attrs["exit_condition_type"] = exit_code
            else:
                raise ValueError(
                    "Valid Exit Conditions for loop are 'Status.SUCCESS/Status.FAILURE/Status.DONT_CARE'."
                )
            return while_loop(name=name, child_tasks=child_tasks, attrs=attrs, **kwargs)


class RunbookTask(BaseTask):
    class Decision:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ssh = decision_task_ssh
        powershell = decision_task_powershell
        escript = EscriptTaskType.DecisionTask
        python = decision_task_python

    class Exec:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        ssh = exec_task_ssh_runbook
        powershell = exec_task_powershell_runbook
        escript = EscriptTaskType.ExecTask
        python = exec_task_python_runbook

    class ResourceTypeOperationTask:
        def __new__(
            cls,
            name,
            resource_type_ref,
            action_ref,
            account_ref=None,
            inarg_list=[],
            target_ref=None,
            output_variables=None,
            tag=None,
            *args,
            **kwargs,
        ):
            return resource_type_operation_task_builder(
                name=name,
                resource_type_ref=resource_type_ref,
                account_ref=account_ref,
                action_ref=action_ref,
                inarg_list=inarg_list,
                target_ref=target_ref,
                output_variables=output_variables,
                tag=tag,
            )

    class ResourceTypeAction(ResourceTypeOperationTask):
        pass

    class Loop:
        def __new__(
            cls,
            iterations,
            name=None,
            child_tasks=[],
            loop_variable="iteration",
            exit_condition=Status.DONT_CARE,
            status_map_list=[],
            **kwargs,
        ):
            attrs = {"iterations": str(iterations), "loop_variable": loop_variable}
            exit_code = EXIT_CONDITION_MAP.get(exit_condition, None)
            if exit_code:
                attrs["exit_condition_type"] = exit_code
            else:
                raise ValueError(
                    "Valid Exit Conditions for loop are 'Status.SUCCESS/Status.FAILURE/Status.DONT_CARE'."
                )
            return while_loop(
                name=name,
                child_tasks=child_tasks,
                attrs=attrs,
                status_map_list=status_map_list,
                **kwargs,
            )

    class HTTP:
        def __new__(
            cls,
            method,
            relative_url=None,
            body=None,
            headers=None,
            secret_headers=None,
            content_type=None,
            status_mapping=None,
            response_code_status_map=[],
            response_paths=None,
            name=None,
            target=None,
            status_map_list=[],
            **kwargs,
        ):
            return http_task_on_endpoint(
                method,
                relative_url=relative_url,
                body=body,
                headers=headers,
                secret_headers=secret_headers,
                content_type=content_type,
                status_mapping=status_mapping,
                response_code_status_map=response_code_status_map,
                response_paths=response_paths,
                name=name,
                target=target,
                status_map_list=status_map_list,
                **kwargs,
            )

        get = http_task_get_on_endpoint
        post = http_task_post_on_endpoint
        put = http_task_put_on_endpoint
        delete = http_task_delete_on_endpoint

    class Input:
        def __new__(cls, timeout=500, name=None, inputs=[]):
            return input_task(timeout=timeout, name=name, inputs=inputs)

    class Confirm:
        def __new__(cls, timeout=500, name=None):
            return confirm_task(timeout=timeout, name=name)

    class VMPowerOn:
        def __new__(cls, name=None, target=None, status_map_list=[], **kwargs):
            return vm_operation(
                name=name,
                type="VM_POWERON",
                target=target,
                status_map_list=status_map_list,
                **kwargs,
            )

    class VMPowerOff:
        def __new__(cls, name=None, target=None, status_map_list=[], **kwargs):
            return vm_operation(
                name=name,
                type="VM_POWEROFF",
                target=target,
                status_map_list=status_map_list,
                **kwargs,
            )

    class VMRestart:
        def __new__(cls, name=None, target=None, status_map_list=[], **kwargs):
            return vm_operation(
                name=name,
                type="VM_RESTART",
                target=target,
                status_map_list=status_map_list,
                **kwargs,
            )

    class NutanixDB:
        """This is the base class of all the NDB Task DSL Support (Not Callable)"""

        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        class PostgresDatabase:
            """This is the base class of all the NDB Postgres Database Action task DSL Support (Not Callable)"""

            def __new__(cls, *args, **kwargs):
                raise TypeError("'{}' is not callable".format(cls.__name__))

            class Create:
                """
                Defines a NDB Postgres Database Create Action task.
                Args:
                    name (str): Name for this task
                    account (Ref.Account): Object of Calm Ref Accounts
                    database_server_config (DatabaseServer.Postgres.Create): Object of NDB Entity DatabaseServer Postgres Create
                    instance_config (Database.Postgres.Create): Object of NDB Entity Database Postgres Create
                    timemachine_config (TimeMachine.Postgres.Create): Object of NDB Entity TimeMachine Postgres Create
                    tag_config (Tag.Postgres.Create): Object of NDB Entity Tag Postgres Create
                    outargs (PostgresDatabaseOutputVariables.Create): Object of Output Variables PostgresDatabaseOutputVariables Create
                Returns:
                    (Task): Resource Type Operation task
                """

                def __new__(
                    cls,
                    name,
                    account,
                    database_server_config,
                    instance_config,
                    timemachine_config,
                    tag_config=None,
                    outargs=None,
                ):
                    (
                        action_variable_list,
                        action_task_name,
                    ) = common_helper.get_variable_list_and_task_name_for_rt_and_action(
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        action_name=NutanixDBConst.ACTION_TYPE.CREATE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    action_task_name_modified = "-".join(
                        action_task_name.lower().split()
                    )

                    inargs = list()
                    common_helper.macro_or_ref_validation(
                        account, Ref.Account, "account should be a instance of Calm Ref"
                    )

                    if not isinstance(
                        database_server_config, DatabaseServer.Postgres.Create
                    ):
                        raise ValueError(
                            "database_server_config should be a instance of DatabaseServer.Postgres.Create"
                        )

                    if not isinstance(instance_config, Database.Postgres.Create):
                        raise ValueError(
                            "instance_config should be a instance of Database.Postgres.Create"
                        )

                    if not isinstance(timemachine_config, TimeMachine.Postgres.Create):
                        raise ValueError(
                            "timemachine_config should be a instance of TimeMachine.Postgres.Create"
                        )
                    if not tag_config:
                        tag_config = Tag.Create()
                    elif not isinstance(tag_config, Tag.Create):
                        raise ValueError(
                            "timemachine_config should be a instance of Tag.Create"
                        )

                    database_server_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    instance_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    timemachine_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    tag_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    output_variables = {}
                    if outargs:
                        if not isinstance(
                            outargs, PostgresDatabaseOutputVariables.Create
                        ):
                            raise ValueError(
                                "outargs should be a instance of PostgresDatabaseOutputVariables.Create"
                            )
                    else:
                        outargs = PostgresDatabaseOutputVariables.Create()

                    output_variables = dict(
                        (v, k) for k, v in outargs.field_values.items()
                    )

                    resource_type_ref = Ref.Resource_Type(
                        name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )
                    action_ref = Ref.ResourceTypeAction(
                        name=NutanixDBConst.ACTION_TYPE.CREATE,
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    return RunbookTask.ResourceTypeOperationTask(
                        name,
                        inarg_list=inargs,
                        resource_type_ref=resource_type_ref,
                        account_ref=account,
                        action_ref=action_ref,
                        output_variables=output_variables,
                        tag=NutanixDBConst.Tag.DATABASE,
                    )

            class Delete:
                """
                Defines a NDB Postgres Database Delete Action task.
                Args:
                    name (str): Name for this task
                    account (Ref.Account): Object of Calm Ref Accounts
                    instance_config (Database.Postgres.Delete): Object of NDB Entity Database Postgres Delete
                Returns:
                    (Task): Resource Type Operation task
                """

                def __new__(cls, name, account, instance_config):
                    (
                        action_variable_list,
                        action_task_name,
                    ) = common_helper.get_variable_list_and_task_name_for_rt_and_action(
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        action_name=NutanixDBConst.ACTION_TYPE.DELETE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    action_task_name_modified = "-".join(
                        action_task_name.lower().split()
                    )

                    inargs = list()
                    common_helper.macro_or_ref_validation(
                        account, Ref.Account, "account should be a instance of Calm Ref"
                    )
                    if not isinstance(instance_config, Database.Postgres.Delete):
                        raise ValueError(
                            "instance_config should be a instance of Database.Postgres.Delete"
                        )

                    instance_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    resource_type_ref = Ref.Resource_Type(
                        name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )
                    action_ref = Ref.ResourceTypeAction(
                        name=NutanixDBConst.ACTION_TYPE.DELETE,
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    rt = RunbookTask.ResourceTypeOperationTask(
                        name,
                        inarg_list=inargs,
                        resource_type_ref=resource_type_ref,
                        account_ref=account,
                        action_ref=action_ref,
                        tag=NutanixDBConst.Tag.DATABASE,
                    )
                    return rt

            class RestoreFromTimeMachine:
                """
                Defines a NDB Postgres Database RestoreFromTimeMachine Action task.
                Args:
                    name (str): Name for this task
                    account (Ref.Account): Object of Calm Ref Accounts
                    instance_config (Database.Postgres.RestoreFromTimeMachine): Object of NDB Entity Database Postgres RestoreFromTimeMachine
                    outargs (PostgresDatabaseOutputVariables.RestoreFromTimeMachine): Object of Output Variables PostgresDatabaseOutputVariables RestoreFromTimeMachine
                Returns:
                    (Task): Resource Type Operation task
                """

                def __new__(
                    cls,
                    name,
                    account,
                    instance_config,
                    outargs=None,
                ):
                    (
                        action_variable_list,
                        action_task_name,
                    ) = common_helper.get_variable_list_and_task_name_for_rt_and_action(
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        action_name=NutanixDBConst.ACTION_TYPE.RESTORE_FROM_TIME_MACHINE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    action_task_name_modified = "-".join(
                        action_task_name.lower().split()
                    )

                    inargs = list()
                    common_helper.macro_or_ref_validation(
                        account, Ref.Account, "account should be a instance of Calm Ref"
                    )

                    if not isinstance(
                        instance_config, Database.Postgres.RestoreFromTimeMachine
                    ):
                        raise ValueError(
                            "instance_config should be a instance of Database.Postgres.RestoreFromTimeMachine"
                        )

                    instance_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    output_variables = {}
                    if outargs:
                        if not isinstance(
                            outargs,
                            PostgresDatabaseOutputVariables.RestoreFromTimeMachine,
                        ):
                            raise ValueError(
                                "outargs should be a instance of PostgresDatabaseOutputVariables.RestoreFromTimeMachine"
                            )
                    else:
                        outargs = (
                            PostgresDatabaseOutputVariables.RestoreFromTimeMachine()
                        )

                    output_variables = dict(
                        (v, k) for k, v in outargs.field_values.items()
                    )

                    resource_type_ref = Ref.Resource_Type(
                        name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )
                    action_ref = Ref.ResourceTypeAction(
                        name=NutanixDBConst.ACTION_TYPE.RESTORE_FROM_TIME_MACHINE,
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    return RunbookTask.ResourceTypeOperationTask(
                        name,
                        inarg_list=inargs,
                        resource_type_ref=resource_type_ref,
                        account_ref=account,
                        action_ref=action_ref,
                        output_variables=output_variables,
                        tag=NutanixDBConst.Tag.DATABASE,
                    )

            class CreateSnapshot:
                def __new__(cls, name, account, instance_config, outargs=None):
                    """
                    Defines a NDB Postgres Database Snapshot Action task.

                    Args:
                        name (str): Name for this task
                        account (Ref.Account): Object of Calm Ref Accounts
                        instance_config (Database.Postgres.CreateSnapshot): Object of NDB Postgres CreateSnapshot

                    Returns:
                        (Task): Resource Type Operation task
                    """
                    (
                        action_variable_list,
                        action_task_name,
                    ) = common_helper.get_variable_list_and_task_name_for_rt_and_action(
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        action_name=NutanixDBConst.ACTION_TYPE.CREATE_SNAPSHOT,
                        provider_name=NutanixDBConst.NDB,
                    )

                    action_task_name_modified = "-".join(
                        action_task_name.lower().split()
                    )

                    inargs = list()
                    common_helper.macro_or_ref_validation(
                        account, Ref.Account, "account should be a instance of Calm Ref"
                    )
                    if not isinstance(
                        instance_config, Database.Postgres.CreateSnapshot
                    ):
                        raise ValueError(
                            "instance_config should be a instance of Database.Postgres.CreateSnapshot"
                        )

                    instance_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    if outargs:
                        if not isinstance(
                            outargs, PostgresDatabaseOutputVariables.CreateSnapshot
                        ):
                            raise ValueError(
                                "outargs should be a instance of PostgresDatabaseOutputVariables.CreateSnapshot"
                            )
                    else:
                        outargs = PostgresDatabaseOutputVariables.CreateSnapshot()
                    output_variables = dict(
                        (v, k) for k, v in outargs.field_values.items()
                    )

                    resource_type_ref = Ref.Resource_Type(
                        name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )
                    action_ref = Ref.ResourceTypeAction(
                        name=NutanixDBConst.ACTION_TYPE.CREATE_SNAPSHOT,
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    rt = RunbookTask.ResourceTypeOperationTask(
                        name,
                        inarg_list=inargs,
                        resource_type_ref=resource_type_ref,
                        account_ref=account,
                        action_ref=action_ref,
                        output_variables=output_variables,
                        tag=NutanixDBConst.Tag.DATABASE,
                    )
                    return rt

            class Clone:
                """
                Defines a NDB Postgres Database Clone Action task.
                Args:
                    name (str): Name for this task
                    account (Ref.Account): Object of Calm Ref Accounts
                    instance_config (Database.Postgres.Clone): Object of NDB Entity Database Postgres Clone
                    timemachine_config (TimeMachine.Postgres.Clone): Object of NDB Entity TimeMachine Postgres Clone
                    tag_config (Tag.Postgres.Clone): Object of NDB Entity Tag Postgres Clone
                Returns:
                    (Task): Resource Type Operation task
                """

                def __new__(
                    cls,
                    name,
                    account,
                    database_server_config,
                    instance_config,
                    timemachine_config,
                    tag_config=None,
                    outargs=None,
                ):
                    (
                        action_variable_list,
                        action_task_name,
                    ) = common_helper.get_variable_list_and_task_name_for_rt_and_action(
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        action_name=NutanixDBConst.ACTION_TYPE.CLONE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    action_task_name_modified = "-".join(
                        action_task_name.lower().split()
                    )

                    inargs = list()
                    common_helper.macro_or_ref_validation(
                        account, Ref.Account, "account should be a instance of Calm Ref"
                    )
                    if not isinstance(instance_config, Database.Postgres.Clone):
                        raise ValueError(
                            "instance_config should be a instance of Database.Postgres.Clone"
                        )

                    if not isinstance(
                        database_server_config, DatabaseServer.Postgres.Clone
                    ):
                        raise ValueError(
                            "database_server_config should be a instance of DatabaseServer.Postgres.Clone"
                        )

                    if not isinstance(timemachine_config, TimeMachine.Postgres.Clone):
                        raise ValueError(
                            "timemachine_config should be a instance of TimeMachine.Postgres.Clone"
                        )

                    if not tag_config:
                        tag_config = Tag.Clone()
                    elif not isinstance(tag_config, Tag.Clone):
                        raise ValueError("tag_config should be a instance of Tag.Clone")

                    database_server_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    instance_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    timemachine_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    tag_config.validate(
                        account,
                        action_variable_list,
                        action_task_name_modified,
                        inargs,
                    )

                    output_variables = {}
                    if outargs:
                        if not isinstance(
                            outargs, PostgresDatabaseOutputVariables.Clone
                        ):
                            raise ValueError(
                                "outargs should be a instance of PostgresDatabaseOutputVariables.Clone"
                            )
                    else:
                        outargs = PostgresDatabaseOutputVariables.Clone()
                    output_variables = dict(
                        (v, k) for k, v in outargs.field_values.items()
                    )
                    resource_type_ref = Ref.Resource_Type(
                        name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    action_ref = Ref.ResourceTypeAction(
                        name=NutanixDBConst.ACTION_TYPE.CLONE,
                        resource_type_name=NutanixDBConst.RESOURCE_TYPE.POSTGRES_DATABASE,
                        provider_name=NutanixDBConst.NDB,
                    )

                    rt = RunbookTask.ResourceTypeOperationTask(
                        name,
                        inarg_list=inargs,
                        resource_type_ref=resource_type_ref,
                        account_ref=account,
                        action_ref=action_ref,
                        output_variables=output_variables,
                        tag=NutanixDBConst.Tag.DATABASE,
                    )
                    return rt
