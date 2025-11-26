import os
import sys
import uuid

from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.ndb import get_schema_file_and_user_attrs
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.builtins import CredentialType
from calm.dsl.decompile.credential import (
    get_cred_var_name,
    render_credential_template,
)
from calm.dsl.decompile.file_handler import get_scripts_dir, get_scripts_dir_key
from calm.dsl.builtins import TaskType
from calm.dsl.db.table_config import AccountCache
from calm.dsl.constants import SUBSTRATE
from calm.dsl.decompile.ref_dependency import (
    get_entity_gui_dsl_name,
    get_power_action_target_substrate,
)

from calm.dsl.builtins.models.task import EXIT_CONDITION_MAP
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_task_template(
    cls,
    entity_context="",
    RUNBOOK_ACTION_MAP={},
    CONFIG_SPEC_MAP={},
    context="",
    secrets_dict=[],
    credentials_list=[],
    rendered_credential_list=[],
    use_calm_var_task=False,
    ignore_cred_dereference_error=False,
):
    LOG.debug("Rendering {} task template".format(cls.name))
    if not isinstance(cls, TaskType):
        raise TypeError("{} is not of type {}".format(cls, TaskType))

    # update entity_context
    entity_context = entity_context + "_Task_" + cls.__name__
    context = (
        context + "task_definition_list." + (getattr(cls, "name", "") or cls.__name__)
    )

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.name
    target = getattr(cls, "target_any_local_reference", None)
    endpoint_target = getattr(cls, "exec_target_reference", None)
    if endpoint_target:  # if target is endpoint target then use that
        user_attrs["target_endpoint"] = render_ref_template(endpoint_target)
    elif target:  # target will be modified to have correct name(DSL name)
        user_attrs["target"] = render_ref_template(target)

    cred = cls.attrs.get("login_credential_local_reference", None)
    if cred:
        try:
            user_attrs["cred"] = "ref({})".format(
                get_cred_var_name(getattr(cred, "name", "") or cred.__name__)
            )
        except ValueError as ve:
            if ignore_cred_dereference_error:
                LOG.debug("Ignoring cred not found error for RTOpTask")
            else:
                raise Exception(ve)
    status_map_list = getattr(cls, "status_map_list", [])
    if status_map_list:
        user_attrs["status_map_list"] = status_map_list

    if cls.type == "EXEC":
        user_attrs["calm_var_task"] = use_calm_var_task
        script_type = cls.attrs["script_type"]
        cls.attrs["script_file"] = create_script_file(
            script_type, cls.attrs["script"], entity_context
        )

        if script_type == "sh":
            schema_file = "task_exec_ssh.py.jinja2"

        elif script_type == "static":
            schema_file = "task_exec_escript.py.jinja2"

        elif script_type == "static_py3":
            schema_file = "task_exec_escript_py3.py.jinja2"

        elif script_type == "npsscript":
            schema_file = "task_exec_powershell.py.jinja2"

        elif script_type == "python_remote":
            schema_file = "task_exec_python.py.jinja2"

    elif cls.type == "SET_VARIABLE":
        variables = cls.attrs.get("eval_variables", None)
        if variables:
            user_attrs["variables"] = variables
        script_type = cls.attrs["script_type"]
        cls.attrs["script_file"] = create_script_file(
            script_type, cls.attrs["script"], entity_context
        )

        if script_type == "sh":
            schema_file = "task_setvariable_ssh.py.jinja2"

        elif script_type == "static":
            schema_file = "task_setvariable_escript.py.jinja2"

        elif script_type == "static_py3":
            schema_file = "task_setvariable_escript_py3.py.jinja2"

        elif script_type == "npsscript":
            schema_file = "task_setvariable_powershell.py.jinja2"

        elif script_type == "python_remote":
            schema_file = "task_setvariable_python.py.jinja2"

    elif cls.type == "DELAY":
        if hasattr(cls, "attrs"):
            user_attrs["delay_seconds"] = cls.attrs.get("interval_secs", 0)
        schema_file = "task_delay.py.jinja2"

    elif cls.type == "SCALING":
        scaling_count = cls.attrs.get("scaling_count", 1)
        if scaling_count:
            user_attrs["scaling_count"] = scaling_count
        scaling_type = cls.attrs["scaling_type"]
        if scaling_type == "SCALEOUT":
            schema_file = "task_scaling_scaleout.py.jinja2"

        elif scaling_type == "SCALEIN":
            schema_file = "task_scaling_scalein.py.jinja2"
    elif cls.type == "HTTP":
        user_attrs["calm_var_task"] = use_calm_var_task
        if "Runbook" in entity_context:
            if user_attrs.get("attrs", {}).get("url", ""):

                # For runbook decompile we are using the RunbookTask as CalmTask
                # But for this case since url is present ( it is the base CalmTask )
                # we import this as CalmVarTask
                user_attrs["calm_var_task"] = True

        attrs = cls.attrs
        user_attrs["headers"] = {}
        user_attrs["secret_headers"] = {}
        user_attrs["response_code_status_map"] = attrs.get(
            "expected_response_params", []
        )

        for var in attrs.get("headers", []):
            var_type = var["type"]
            if var_type == "LOCAL":
                user_attrs["headers"][var["name"]] = var["value"]

            elif var_type == "SECRET":
                user_attrs["secret_headers"][var["name"]] = var["value"]
                secrets_dict.append(
                    {
                        "context": context + ".headers." + var["name"],
                        "secret_name": var["name"],
                        "secret_value": var["value"],
                    }
                )

        # Store auth objects
        auth_obj = attrs.get("authentication", {})
        auth_type = auth_obj.get("type", "")
        if auth_type == "basic_with_cred":
            auth_cred = auth_obj.get("credential_local_reference", None)
            if auth_cred:
                try:
                    user_attrs["cred"] = "ref({})".format(
                        get_cred_var_name(
                            getattr(auth_cred, "name", "") or auth_cred.__name__
                        )
                    )
                except ValueError as ve:
                    if ignore_cred_dereference_error:
                        LOG.debug("Ignoring cred not found error for RTOpTask")
                    else:
                        raise Exception(ve)
        elif auth_type == "basic":
            cred_dict = {
                "username": auth_obj["username"],
                "password": auth_obj["password"],
                "type": "PASSWORD",
                "name": "Credential" + str(uuid.uuid4())[:8],
            }
            cred = CredentialType.decompile(cred_dict)
            rendered_credential_list.append(
                render_credential_template(
                    cred,
                    context="PROVIDER"
                    if (
                        entity_context.startswith("CloudProvider")
                        or entity_context.startswith("ResourceType")
                    )
                    else "BP",
                )
            )
            cred = get_cred_var_name(cred.name)
            user_attrs["credentials_list"] = cred
            cred_dict["name_in_file"] = cred
            credentials_list.append(cred_dict)

        user_attrs["response_paths"] = attrs.get("response_paths", {})
        method = attrs["method"]

        if (method == "POST" or method == "PUT") and not cls.attrs["request_body"]:
            cls.attrs["request_body"] = {}

        if method == "GET":
            schema_file = "task_http_get.py.jinja2"

        elif method == "POST":
            schema_file = "task_http_post.py.jinja2"

        elif method == "PUT":
            schema_file = "task_http_put.py.jinja2"

        elif method == "DELETE":
            schema_file = "task_http_delete.py.jinja2"

        if method != "GET" and cls.attrs["request_body"] != None:
            cls.attrs["request_body"] = repr(cls.attrs["request_body"])

    elif cls.type == "CALL_RUNBOOK":
        is_power_action = False
        runbook = cls.attrs["runbook_reference"]
        runbook_name = getattr(runbook, "name", "") or runbook.__name__

        # constructing user_attrs for power action runbooks of substrate
        for action_name in list(SUBSTRATE.VM_POWER_ACTIONS_REV.keys()):
            if action_name in runbook_name and "substrate" in runbook_name:
                gui_substrate_name = get_power_action_target_substrate(runbook_name)

                # mapping correct dsl class name using gui name found above
                substrate = get_entity_gui_dsl_name(gui_substrate_name)
                if not substrate:
                    raise ValueError("Target substrate not found")
                user_attrs = {
                    "name": cls.name,
                    "action": SUBSTRATE.VM_POWER_ACTIONS_REV[action_name],
                    "target_substrate": substrate,
                    "target": target.name,
                }
                is_power_action = True
                break

        # fallback to default user_attrs for backward compatibility
        if not is_power_action:
            user_attrs = {
                "name": cls.name,
                "action": RUNBOOK_ACTION_MAP[runbook_name],
                "target": target.name,
            }

        if is_power_action:
            schema_file = "task_power_action_call_runbook.py.jinja2"
        else:
            schema_file = "task_call_runbook.py.jinja2"

    elif cls.type == "CALL_CONFIG":
        config_name = cls.attrs["config_spec_reference"]
        user_attrs = {
            "name": cls.name,
            "config": CONFIG_SPEC_MAP[config_name]["global_name"],
        }
        schema_file = "task_call_config.py.jinja2"
    elif cls.type == "RT_OPERATION":
        schema_file, user_attrs = get_schema_file_and_user_attrs(
            cls.name,
            cls.attrs,
            credentials_list=credentials_list,
            rendered_credential_list=rendered_credential_list,
        )
    elif cls.type == "DECISION":
        script_type = cls.attrs["script_type"]
        cls.attrs["script_file"] = create_script_file(
            script_type, cls.attrs["script"], entity_context
        )
        script_type = cls.attrs["script_type"]
        if script_type == "sh":
            schema_file = "task_decision_ssh.py.jinja2"

        elif script_type == "static":
            schema_file = "task_decision_escript.py.jinja2"

        elif script_type == "static_py3":
            schema_file = "task_decision_escript_py3.py.jinja2"

        elif script_type == "npsscript":
            schema_file = "task_decision_powershell.py.jinja2"

        elif script_type == "python_remote":
            schema_file = "task_decision_python.py.jinja2"

    elif cls.type == "WHILE_LOOP":
        exit_condition_type = cls.attrs["exit_condition_type"]
        for key in EXIT_CONDITION_MAP:
            if EXIT_CONDITION_MAP[key] == exit_condition_type:
                cls.attrs["exit_condition_type"] = key
        schema_file = "task_while_loop.py.jinja2"
    elif cls.type == "VM_POWERON":
        schema_file = "task_vm_power_on.py.jinja2"
    elif cls.type == "VM_POWEROFF":
        schema_file = "task_vm_power_off.py.jinja2"
    elif cls.type == "VM_RESTART":
        schema_file = "task_vm_restart.py.jinja2"
    else:
        LOG.error("Task type does not match any known types")
        sys.exit("Invalid task {}".format(cls.type))

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()


def create_script_file(script_type, script="", entity_context=""):
    """create the script file and return the file location"""

    # Use task context for unique names
    file_name = entity_context
    scripts_dir = get_scripts_dir()

    if script_type == "sh":
        file_name += ".sh"

    elif script_type == "npsscript":
        file_name += ".ps1"

    elif script_type in ["static", "static_py3", "python_remote"]:
        file_name += ".py"

    else:
        raise TypeError("Script Type {} not supported".format(script_type))

    file_location = os.path.join(scripts_dir, file_name)
    with open(file_location, "w+") as fd:
        fd.write(script)

    dsl_file_location = "os.path.join('{}', '{}')".format(
        get_scripts_dir_key(), file_name
    )
    return dsl_file_location
