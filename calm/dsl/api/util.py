import copy
import json
import sys
import os
import click

from urllib.parse import urlparse
from copy import deepcopy

from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context
from calm.dsl.constants import DSL_CONFIG, MARKETPLACE, MULTICONNECT, FLAGS
from calm.dsl.api.resource import get_resource_api
from calm.dsl.api.connection import MultiConnection

LOG = get_logging_handle(__name__)


def get_secrets_from_context(decompiled_secrets, context):
    """Finds all the secrets by context of the current secret"""

    filtered_secrets = dict()

    if context in decompiled_secrets:
        filtered_secrets = copy.deepcopy(decompiled_secrets.get(context, {}))

    return filtered_secrets


def is_secret_modified(filtered_secrets, name, value):
    """
    Check if the secret is modified or not
    Secret is considered modified if its name/value has changed
    """

    if name in filtered_secrets and filtered_secrets[name] != value:
        LOG.warning("Value of decompiled secret variable {} is modified".format(name))
        LOG.debug(
            "Original value: {}, New value: {}".format(filtered_secrets[name], value)
        )
        return True

    elif name not in filtered_secrets:
        return True

    return False


def strip_secrets(
    resources,
    secret_map,
    secret_variables,
    object_lists=[],
    objects=[],
    decompiled_secrets=[],
    not_stripped_secrets=[],
):
    """
    Strips secrets from the resources
    Args:
        resources (dict): request payload
        secret_map (dict): credential secret values
        secret_variables (list): list of secret variables
    Returns: None
    """

    # Remove creds before upload
    strip_credentials(resources, decompiled_secrets, secret_map)

    # Remove creds from HTTP endpoints resources
    filtered_decompiled_secret_auth_creds = get_secrets_from_context(
        decompiled_secrets, "authentication"
    )
    auth = resources.get("authentication", {}) or {}
    if auth.get("type", None) == "basic":
        if is_secret_modified(
            filtered_decompiled_secret_auth_creds, auth["username"], auth["password"]
        ):
            name = auth["username"]
            secret_map[name] = auth.pop("password", {})
            auth["password"] = {"attrs": {"is_secret_modified": False, "value": None}}

    for object_list in object_lists:
        for obj_idx, obj in enumerate(resources.get(object_list, []) or []):
            strip_all_secret_variables(
                [object_list, obj_idx],
                obj,
                decompiled_secrets,
                secret_variables,
                not_stripped_secrets,
            )

            # Currently, deployment actions and variables are unsupported.
            # Uncomment the following lines if and when the API does support them.
            # if object_list == "app_profile_list":
            #     for dep_idx, dep in enumerate(obj["deployment_create_list"]):
            #         strip_all_secret_variables(
            #             [object_list, obj_idx, "deployment_create_list", dep_idx],
            #             dep, decompiled_secrets, secret_variables, not_stripped_secrets,
            #         )

    for obj in objects:
        strip_all_secret_variables(
            [obj],
            resources.get(obj, {}),
            decompiled_secrets,
            secret_variables,
            not_stripped_secrets,
        )


def strip_provider_secrets(
    provider_name,
    provider_resources,
    secret_map,
    secret_variables,
    decompiled_secrets=[],
    not_stripped_secrets=[],
):
    """
    Strips secrets from provider resources
    Args:
        provider_resources (dict): request payload
        secret_map (dict): credential secret values
        secret_variables (list): list of secret variables
    Returns: None
    """
    # Remove creds before upload
    strip_credentials(provider_resources, decompiled_secrets, secret_map)

    for obj_idx, obj in enumerate(
        provider_resources.get("resource_type_list", []) or []
    ):
        path_list = ["resource_type_list", obj_idx]
        strip_all_secret_variables(
            path_list,
            obj,
            decompiled_secrets,
            secret_variables,
            not_stripped_secrets,
        )
        strip_entity_secret_variables(
            path_list,
            obj,
            decompiled_secrets,
            secret_variables,
            not_stripped_secrets,
            context=path_list[0],
            field_name="schema_list",
        )

    # NOTE: Not calling strip_all_secret_variables for provider spec because the context
    # building logic assumes heavily that actions, variables, runbooks etc..,. always
    # belong to an entity thats part of a list. Eg: profile_list, substrate_list etc..,.

    # Strip secrets in endpoint schema, auth schema, attribute & test account variables
    strip_entity_secret_variables(
        [],
        provider_resources,
        decompiled_secrets,
        secret_variables,
        not_stripped_secrets,
        context="variable_list",
    )
    strip_entity_secret_variables(
        [],
        provider_resources,
        decompiled_secrets,
        secret_variables,
        not_stripped_secrets,
        context="auth_schema_list",
        field_name="auth_schema_list",
    )
    strip_entity_secret_variables(
        ["endpoint_schema"],
        provider_resources.get("endpoint_schema", {}),
        decompiled_secrets,
        secret_variables,
        not_stripped_secrets,
        context="endpoint_schema_list",
    )
    strip_entity_secret_variables(
        ["test_account", "data"],
        provider_resources.get("test_account", {}).get("data", {}),
        decompiled_secrets,
        secret_variables,
        not_stripped_secrets,
        context="test_account_variable_list",
    )

    # Strip secrets in provider actions & their runbooks
    strip_action_secret_variables(
        [],
        provider_resources,
        decompiled_secrets,
        secret_variables,
        not_stripped_secrets,
        context="action_list",
    )


def strip_entity_secret_variables(
    path_list,
    obj,
    decompiled_secrets,
    secret_variables,
    not_stripped_secrets,
    field_name="variable_list",
    context="",
):

    if field_name != "headers" and obj.get("name", None):
        context = context + "." + obj["name"] + "." + field_name

    filtered_decompiled_secrets = get_secrets_from_context(decompiled_secrets, context)

    for var_idx, variable in enumerate(obj.get(field_name, []) or []):
        if variable["type"] == "SECRET":
            if is_secret_modified(
                filtered_decompiled_secrets,
                variable.get("name", None),
                variable.get("value", None),
            ):
                secret_variables.append(
                    (
                        path_list + [field_name, var_idx],
                        variable.pop("value"),
                        variable.get("name", None),
                    )
                )
                variable["attrs"] = {
                    "is_secret_modified": False,
                    "secret_reference": None,
                }
            elif variable.get("value", None):
                not_stripped_secrets.append(
                    (path_list + [field_name, var_idx], variable["value"])
                )
        # For dynamic variables having http task with auth
        opts = variable.get("options", None)
        auth = None
        if opts:
            attrs = opts.get("attrs", None)
            if attrs:
                auth = attrs.get("authentication", None)
        if auth and auth.get("auth_type") == "basic":
            basic_auth = auth.get("basic_auth")
            username = basic_auth.get("username")
            password = basic_auth.pop("password")
            secret_variables.append(
                (
                    path_list
                    + [
                        field_name,
                        var_idx,
                        "options",
                        "attrs",
                        "authentication",
                        "basic_auth",
                        "password",
                    ],
                    password.get("value", None),
                    username,
                )
            )
            basic_auth["password"] = {
                "value": None,
                "attrs": {"is_secret_modified": False},
            }


def strip_action_secret_variables(
    path_list,
    obj,
    decompiled_secrets,
    secret_variables,
    not_stripped_secrets,
    context="",
):

    if not context:
        context = path_list[0] + "." + obj["name"] + ".action_list"

    for action_idx, action in enumerate(obj.get("action_list", []) or []):
        var_context = context + "." + action["name"]
        runbook = action.get("runbook", {}) or {}
        var_runbook_context = var_context + ".runbook"

        if not runbook:
            return
        strip_entity_secret_variables(
            path_list + ["action_list", action_idx, "runbook"],
            runbook,
            decompiled_secrets,
            secret_variables,
            not_stripped_secrets,
            context=var_runbook_context,
        )

        tasks = runbook.get("task_definition_list", [])

        var_runbook_task_context = (
            var_runbook_context + "." + runbook["name"] + ".task_definition_list"
        )

        for task_idx, task in enumerate(tasks):
            if task.get("type", None) != "HTTP":
                continue
            auth = (task.get("attrs", {}) or {}).get("authentication", {}) or {}

            var_runbook_task_name_context = (
                var_runbook_task_context + "." + task["name"]
            )

            var_runbook_task_name_basic_auth_context = (
                var_runbook_task_context + "." + task["name"] + ".basic_auth"
            )

            if auth.get("auth_type", None) == "basic":

                filtered_decompiled_secrets = get_secrets_from_context(
                    decompiled_secrets, var_runbook_task_name_basic_auth_context
                )

                if is_secret_modified(
                    filtered_decompiled_secrets,
                    auth.get("basic_auth", {}).get("username", None),
                    auth.get("basic_auth", {}).get("password", {}).get("value", None),
                ):
                    secret_variables.append(
                        (
                            path_list
                            + [
                                "action_list",
                                action_idx,
                                "runbook",
                                "task_definition_list",
                                task_idx,
                                "attrs",
                                "authentication",
                                "basic_auth",
                                "password",
                            ],
                            auth["basic_auth"]["password"].pop("value"),
                            auth.get("basic_auth", {}).get("username", None),
                        )
                    )
                    auth["basic_auth"]["password"] = {
                        "attrs": {
                            "is_secret_modified": False,
                            "secret_reference": None,
                        }
                    }
                elif (
                    auth.get("basic_auth", None)
                    .get("password", None)
                    .get("value", None)
                ):
                    not_stripped_secrets.append(
                        (
                            path_list
                            + [
                                "action_list",
                                action_idx,
                                "runbook",
                                "task_definition_list",
                                task_idx,
                                "attrs",
                                "authentication",
                                "basic_auth",
                                "password",
                            ],
                            auth["basic_auth"]["password"]["value"],
                        )
                    )

            http_task_headers = (task.get("attrs", {}) or {}).get("headers", []) or []
            if http_task_headers:
                strip_entity_secret_variables(
                    path_list
                    + [
                        "action_list",
                        action_idx,
                        "runbook",
                        "task_definition_list",
                        task_idx,
                        "attrs",
                    ],
                    task["attrs"],
                    decompiled_secrets,
                    secret_variables,
                    not_stripped_secrets,
                    field_name="headers",
                    context=var_runbook_task_name_context + ".headers",
                )


def strip_runbook_secret_variables(
    path_list,
    obj,
    decompiled_secrets,
    secret_variables,
    not_stripped_secrets,
):

    context = path_list[0] + "." + obj["name"] + ".task_definition_list"

    tasks = obj.get("task_definition_list", [])
    original_path_list = copy.deepcopy(path_list)
    for task_idx, task in enumerate(tasks):
        path_list = original_path_list
        if task.get("type", None) == "RT_OPERATION":
            path_list = path_list + [
                "task_definition_list",
                task_idx,
                "attrs",
            ]
            strip_entity_secret_variables(
                path_list,
                task["attrs"],
                decompiled_secrets,
                secret_variables,
                not_stripped_secrets,
                field_name="inarg_list",
            )
            continue
        elif task.get("type", None) != "HTTP":
            continue
        auth = (task.get("attrs", {}) or {}).get("authentication", {}) or {}
        if auth.get("auth_type", None) == "basic":
            path_list = path_list + ["runbook"]

        path_list = path_list + [
            "task_definition_list",
            task_idx,
            "attrs",
        ]
        var_task_context = context + "." + task["name"]

        strip_authentication_secret_variables(
            path_list,
            task.get("attrs", {}) or {},
            decompiled_secrets,
            secret_variables,
            not_stripped_secrets,
            context=var_task_context,
        )

        if not (task.get("attrs", {}) or {}).get("headers", []) or []:
            continue
        strip_entity_secret_variables(
            path_list,
            task["attrs"],
            decompiled_secrets,
            secret_variables,
            not_stripped_secrets,
            field_name="headers",
            context=var_task_context + ".headers",
        )


def strip_authentication_secret_variables(
    path_list,
    obj,
    decompiled_secrets,
    secret_variables,
    not_stripped_secrets,
    context="",
):

    basic_auth_context = context + "." + obj.get("name", "") + ".basic_auth"

    filtered_decompiled_secrets = get_secrets_from_context(
        decompiled_secrets, basic_auth_context
    )

    auth = obj.get("authentication", {})
    if auth.get("auth_type", None) == "basic":

        if is_secret_modified(
            filtered_decompiled_secrets,
            auth.get("password", {}).get("name", None),
            auth.get("password", {}).get("value", None),
        ):
            secret_variables.append(
                (
                    path_list + ["authentication", "basic_auth", "password"],
                    auth["password"].pop("value"),
                    auth.get("password", {}).get("name", None),
                )
            )
            auth["password"] = {"attrs": {"is_secret_modified": False}}
        elif auth.get("password", None).get("value", None):
            not_stripped_secrets.append(
                (
                    path_list + ["authentication", "basic_auth", "password"],
                    auth["password"]["value"],
                )
            )


def strip_all_secret_variables(
    path_list,
    obj,
    decompiled_secrets,
    secret_variables,
    not_stripped_secrets,
):
    strip_entity_secret_variables(
        path_list,
        obj,
        decompiled_secrets,
        secret_variables,
        not_stripped_secrets,
        context=path_list[0],
    )
    strip_action_secret_variables(
        path_list, obj, decompiled_secrets, secret_variables, not_stripped_secrets
    )
    strip_runbook_secret_variables(
        path_list, obj, decompiled_secrets, secret_variables, not_stripped_secrets
    )
    strip_authentication_secret_variables(
        path_list,
        obj,
        decompiled_secrets,
        secret_variables,
        not_stripped_secrets,
        context=path_list[0],
    )


def strip_credentials(resources, decompiled_secrets, secret_map):
    creds = resources.get("credential_definition_list", []) or []
    filtered_decompiled_secret_credentials = get_secrets_from_context(
        decompiled_secrets, "credential_definition_list"
    )

    for cred in creds:
        name = cred["name"]
        value = cred["secret"]["value"]

        if is_secret_modified(filtered_decompiled_secret_credentials, name, value):
            secret_map[name] = cred.pop("secret", {})
            # Explicitly set defaults so that secret is not created at server
            # TODO - Fix bug in server: {} != None
            cred["secret"] = {
                "attrs": {"is_secret_modified": False, "secret_reference": None}
            }


# Handling vmware secrets
def strip_vmware_secrets(
    path_list, obj, secret_variables=[], decompiled_secrets=[], not_stripped_secrets=[]
):
    path_list.extend(["create_spec", "resources", "guest_customization"])
    obj = obj["create_spec"]["resources"]["guest_customization"]
    vmware_secrets_context = "create_spec.resources.guest_customization.windows_data"

    if obj.get("windows_data", {}):
        path_list.append("windows_data")
        obj = obj["windows_data"]
        if not obj:
            return

        vmware_secrets_admin_context = (
            vmware_secrets_context
            + "windows_data"
            + ".password."
            + obj["password"].get("name", "")
        )
        filtered_decompiled_vmware_secrets = get_secrets_from_context(
            decompiled_secrets, vmware_secrets_admin_context
        )

        # Check for admin_password
        if obj.get("password", {}):
            if is_secret_modified(
                filtered_decompiled_vmware_secrets,
                obj["password"].get("name", ""),
                obj["password"].get("value", None),
            ):
                secret_variables.append(
                    (
                        path_list + ["password"],
                        obj["password"].pop("value", ""),
                        obj["password"].get("name", ""),
                    )
                )
                obj["password"]["attrs"] = {
                    "is_secret_modified": False,
                    "secret_reference": None,
                }
            else:
                not_stripped_secrets.append(
                    (path_list + ["password"], obj["password"].get("value", ""))
                )

        # Now check for domain password
        if obj.get("is_domain", False):
            if obj.get("domain_password", {}):
                vmware_secrets_domain_context = (
                    vmware_secrets_context
                    + "windows_data"
                    + ".domain_password."
                    + obj["domain_password"].get("name", "")
                )

                filtered_decompiled_vmware_secrets = get_secrets_from_context(
                    decompiled_secrets, vmware_secrets_domain_context
                )
                if is_secret_modified(
                    filtered_decompiled_vmware_secrets,
                    obj["domain_password"].get("name", ""),
                    obj["domain_password"].get("value", None),
                ):
                    secret_variables.append(
                        (
                            path_list + ["domain_password"],
                            obj["domain_password"].pop("value", ""),
                            obj["domain_password"]["name"],
                        )
                    )
                    obj["domain_password"]["attrs"] = {
                        "is_secret_modified": False,
                        "secret_reference": None,
                    }
                else:
                    not_stripped_secrets.append(
                        (
                            path_list + ["domain_password"],
                            obj["domain_password"].pop("value", ""),
                        )
                    )


def patch_secrets(resources, secret_map, secret_variables, existing_secrets=[]):
    """
    Patches the secrests to payload
    Args:
        resources (dict): resources in API request payload
        secret_map (dict): credential secret values
        secret_variables (list): list of secret variables
    Returns:
        dict: payload with secrets patched
    """

    # Add creds back
    creds = resources.get("credential_definition_list", [])
    for cred in creds:
        name = cred["name"]
        if name in secret_map:
            cred["secret"] = secret_map[name]

    # Add creds back for HTTP endpoint
    auth = resources.get("authentication", {})
    username = auth.get("username", "")
    if (username) and (username in secret_map):
        auth["password"] = secret_map[username]

    # Do not modify already existing secrets
    for path, secret in existing_secrets:
        variable = resources
        for sub_path in path:
            if isinstance(variable, dict) and sub_path not in variable:
                break
            variable = variable[sub_path]
        else:
            variable["attrs"] = {"is_secret_modified": False}

    if secret_variables:
        for secret_var_data in secret_variables:
            path = secret_var_data[0]
            secret = secret_var_data[1]
            variable = resources
            for sub_path in path:
                if isinstance(variable, dict) and sub_path not in variable:
                    break
                variable = variable[sub_path]
            else:
                variable["attrs"] = {"is_secret_modified": True}
                variable["value"] = secret

    return resources


def get_auth_info(api_key_location):
    """
    Reads name+token from specified api-key file (if it exists) as username+password
    Else it reads username+password from config.
    Args:
        api_key_location (str): location of api-key
    Returns:
        dict: containing username and password for authentication.
    """

    if api_key_location not in [None, DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME]:
        if not os.path.exists(api_key_location):
            LOG.error("{} not found".format(api_key_location))
            sys.exit(-1)

        with open(api_key_location, "r") as f:
            auth_creds = f.read()
            auth_creds = json.loads(auth_creds)

        if not auth_creds.get("name"):
            LOG.error(
                "Badly formatted key file. Key name not present in {}".format(
                    api_key_location
                )
            )
            sys.exit(-1)

        if not auth_creds.get("token"):
            LOG.error(
                "Badly formatted key file. Token not present in {}".format(
                    api_key_location
                )
            )
            sys.exit(-1)

        cred = {"username": auth_creds.get("name"), "password": auth_creds.get("token")}
    # Read username/password from config when api-key is not supplied
    else:
        context = get_context()
        server_config = context.get_server_config()
        cred = {
            "username": server_config.get("pc_username"),
            "password": server_config.get("pc_password"),
        }

    return cred


def _create_task_name_substrate_map(bp_payload, entity_type, **kwargs):
    vm_power_action_uuid_substrate_map = kwargs.get(
        "vm_power_action_uuid_substrate_map", {}
    )
    task_name_substrate_map = kwargs.get("task_name_substrate_map", {})

    entity_list = bp_payload["spec"]["resources"][entity_type]
    for entity in entity_list:
        entity_name = entity.get("name")
        for action in entity.get("action_list", []):
            action_name = action.get("name")
            runbook = action.get("runbook", {})
            if not runbook:
                continue
            for task in runbook.get("task_definition_list", []):
                task_name = task.get("name")
                if task.get("type", "") == "CALL_RUNBOOK" and task.get("attrs", {}):
                    uuid = task["attrs"]["runbook_reference"].get("uuid", "")
                    if not uuid:
                        continue
                    task_name_substrate_map[
                        "{}_{}_{}".format(entity_name, action_name, task_name)
                    ] = vm_power_action_uuid_substrate_map.get(uuid, "")

        for config in entity.get("patch_list", []):
            config_name = config.get("name")
            runbook = config.get("runbook", {})
            if not runbook:
                continue
            for task in runbook.get("task_definition_list", []):
                task_name = task.get("name")
                if task.get("type", "") == "CALL_RUNBOOK" and task.get("attrs", {}):
                    uuid = task["attrs"]["runbook_reference"].get("uuid", "")
                    if not uuid:
                        continue
                    task_name_substrate_map[
                        "{}_{}_{}".format(entity_name, config_name, task_name)
                    ] = vm_power_action_uuid_substrate_map.get(uuid, "")


def _create_reference_runbook_substrate_map(exported_bp_payload, entity_type, **kwargs):
    reference_runbook_to_substrate_map = kwargs.get(
        "reference_runbook_to_substrate_map", {}
    )
    task_name_substrate_map = kwargs.get("task_name_substrate_map", {})

    entity_list = exported_bp_payload["spec"]["resources"][entity_type]
    for entity in entity_list:
        entity_name = entity.get("name")
        for action in entity.get("action_list", []):
            action_name = action.get("name")
            runbook = action.get("runbook", {})
            if not runbook:
                continue
            for task in runbook.get("task_definition_list", []):
                task_name = task.get("name")
                if task.get("type", "") == "CALL_RUNBOOK" and task.get("attrs", {}):
                    rb_name = task["attrs"]["runbook_reference"].get("name", "")
                    task_ref = "{}_{}_{}".format(entity_name, action_name, task_name)
                    if (
                        task_ref in task_name_substrate_map
                        and task_name_substrate_map[task_ref]
                    ):
                        reference_runbook_to_substrate_map[
                            rb_name
                        ] = task_name_substrate_map[task_ref]

        for config in entity.get("patch_list", []):
            config_name = config.get("name")
            runbook = config.get("runbook", {})
            if not runbook:
                continue
            for task in runbook.get("task_definition_list", []):
                task_name = task.get("name")
                if task.get("type", "") == "CALL_RUNBOOK" and task.get("attrs", {}):
                    rb_name = task["attrs"]["runbook_reference"].get("name", "")
                    if not rb_name:
                        continue
                    task_ref = "{}_{}_{}".format(entity_name, config_name, task_name)
                    if (
                        task_ref in task_name_substrate_map
                        and task_name_substrate_map[task_ref]
                    ):
                        reference_runbook_to_substrate_map[
                            rb_name
                        ] = task_name_substrate_map[task_ref]


def vm_power_action_target_map(bp_payload, exported_bp_payload):
    """
    Args:
        bp_payload (dict): bp payload response from client.blueprint.read call
        exported_bp_payload (dict): bp payload response from client.blueprint.export_file call

        exported_bp_payload contains actual runbook name as reference which is called for any vm power action.
        This payload only contains spec but power action reside in 'status' of res payload.
        So, substrate of actual runbook name can't be found directly.

        bp_payload contains 'status' of res so substrate can be fetched from it. In this payload,
        runbook name is alias to actual runbook used as reference for vm power action. So,
        runbook uuid will be consumed to establish link between runbook reference and it's substrate.

    Algo:
        Step 1: Create a map of power action runbook uuid and it's parent substrate
        Step 2: Create map of task name calling above rb and substrate name by consuming rb uuid
                rb uuid links task name -> rb uuid -> substrate name
        Step 3: Create map of actual rb name calling above rb in exported bp_payload to substrate name
                task name will be consumed in this process.
                rb name -> task name -> substrate name

    Returns:
        reference_runbook_to_substrate_map (dict): runbook name to substrate name map for vm
        power action runbook used as reference inside a task, e.g.
         reference_runbook_to_substrate_map = {
            "rb_name1": substrate_name
            "rb_name2": substrate2_name
        }
    """

    # holds vm power action uuid to it's parent substrate name mapping
    vm_power_action_uuid_substrate_map = {}
    """
        vm_power_action_uuid_substrate_map = {
            "<power_action_uuid>": substrate_name
        }
    """

    # holds target substrate for referenced power action runbook of a task
    task_name_substrate_map = {}
    """
        task_name_substrate_map = {
            "<profile_name>_<action_name>_<task_name>": substrate_name
        }
        "<profile_name>_<action_name>_<task_name>" key is used to uniquely identify a task even if they are of same name
    """

    # task name to substrate map holds target substrate for referenced power action runbook of a task
    reference_runbook_to_substrate_map = {}
    """
        reference_runbook_to_substrate_map = {
            "rb_name1": substrate_name,
            "rb_name2": substrate2_name
        }
    """

    substrate_def_list = bp_payload["status"]["resources"]["substrate_definition_list"]
    for substrate in substrate_def_list:
        substrate_name = substrate.get("name")
        for action in substrate.get("action_list", []):
            runbook_id = action.get("runbook", {}).get("uuid", "")
            vm_power_action_uuid_substrate_map[runbook_id] = substrate_name

    kwargs = {
        "vm_power_action_uuid_substrate_map": vm_power_action_uuid_substrate_map,
        "task_name_substrate_map": task_name_substrate_map,
        "reference_runbook_to_substrate_map": reference_runbook_to_substrate_map,
    }
    entity_type_list = [
        "substrate_definition_list",
        "service_definition_list",
        "app_profile_list",
        "package_definition_list",
    ]
    for entity_type in entity_type_list:
        _create_task_name_substrate_map(bp_payload, entity_type, **kwargs)

    for entity_type in entity_type_list:
        _create_reference_runbook_substrate_map(
            exported_bp_payload, entity_type, **kwargs
        )

    return reference_runbook_to_substrate_map


def strip_patch_config_tasks(resources):
    """
    Strips out patch config tasks from patch list
    Args:
        resources (dict): resources dict of blueprint
    Returns:
        profile_patch_config_tasks (dict): dictionary of dictionary containing
        user defined tasks at patch config level for each profile.

        e.g. if Profile1 contains patch_config1, patch_config2 having 3 and 2 user defined tasks respectively like:
            Profile1 -> patch_config1 -> Task1, Task2, Task3
                        patch_config2 -> Task4, Task5

        then return value of this function is:
            profile_patch_config_tasks = {
                "Profile1": {
                    “patch_config1” : [Task1, Task2, Task3],
                    "patch_config2" : [Task4, Task5]
                }
            }
    """

    # contains list of dictionary of patch list for multiple profile
    profile_patch_config_tasks = {}

    for profile in resources.get("app_profile_list", []):
        # dictionary to hold muliple patch config to it's tasks mapping
        patch_config_task_list_map = {}

        for patch_config in profile.get("patch_list", []):
            tasks = patch_config.get("runbook", {}).pop("task_definition_list", [])
            patch_config_task_list_map[patch_config.get("name")] = tasks

            # Strips out runbook holding patch config tasks in patch list
            patch_config.pop("runbook", "")

        profile_patch_config_tasks[profile.get("name")] = patch_config_task_list_map

    return profile_patch_config_tasks


def add_patch_config_tasks(
    resources,
    app_profile_list,
    profile_patch_config_tasks,
    service_name_uuid_map,
):
    """
    Adds patch config tasks to patch list payload for each profile in bp.

    Args:
        resources (dict): resources fetch from "spec" of bp payload
        app_profile_list (list): profile list fetched from "status" of bp payload
        (because system defined patch config tasks are present in status)
        profile_patch_config_tasks (list): returned from strip_patch_config_tasks function call.
        Contains user defined patch config tasks from patch list for all profile.
        service_name_uuid_map (dict): service name to its uuid map

    Step1: Reads patch config runbook from app_profile_list containing system defined
    patch config tasks.
    Step2: Update this runbook with user defined tasks
    Step3: Attach this runbook to patch config runbook of resources fetched from spec
    """

    for profile in app_profile_list:

        # profile level map holding task name uuid map for each config
        cur_profile_task_name_uuid_map = {}
        """
            cur_profile_task_name_uuid_map = {
                "patch_config1": {
                    "task1": "<uuid>",
                    "task2": "<uuid>",
                    "task3": "<uuid>"
                },
                "patch_config2": {
                    "task4": "<uuid>",
                    "task5": "<uuid>",
                }
            }
        """

        # holds patch config tasks for current profile
        patch_config_task_list_map = profile_patch_config_tasks.get(profile["name"], {})

        # iterate over all tasks in patch list and create task_name_uuid_map_list
        for config_name, task_list in patch_config_task_list_map.items():
            task_name_uuid_map = {}
            # cur_profile_patch_config_tasks[config_name] = task_list
            for _task in task_list:
                task_name_uuid_map[_task["name"]] = _task["uuid"]

            cur_profile_task_name_uuid_map[config_name] = task_name_uuid_map

        # append patch config tasks to system defined tasks in patch config
        for patch_config in profile.get("patch_list", []):
            patch_config_runbook = patch_config.get("runbook", {})
            if not patch_config_runbook:
                continue

            # removing additional attributes of patch runbook
            patch_config_runbook.pop("state", "")
            patch_config_runbook.pop("message_list", "")

            system_tasks = patch_config_runbook.get("task_definition_list", [])
            system_dag_task = system_tasks[0]
            config_name = patch_config.get("name")

            for custom_task in patch_config_task_list_map[config_name]:
                if "target_any_local_reference" in custom_task:
                    service_name = custom_task["target_any_local_reference"]["name"]
                    service_uuid = service_name_uuid_map.get(service_name, None)
                    if not service_uuid:
                        LOG.error(
                            "Service {} not added properly in blueprint.".format(
                                service_name
                            )
                        )
                        sys.exit(-1)
                    custom_task["target_any_local_reference"]["uuid"] = service_uuid

                # add all patch config tasks to task definition list
                if custom_task["type"] != "DAG":
                    system_tasks.append(custom_task)
                    system_dag_task["child_tasks_local_reference_list"].append(
                        {
                            "kind": "app_task",
                            "name": custom_task["name"],
                            "uuid": custom_task["uuid"],
                        }
                    )

                # create edge from patch config dag to tasks
                elif custom_task["type"] == "DAG":

                    user_first_task_name = custom_task[
                        "child_tasks_local_reference_list"
                    ][0]["name"]

                    # edge from patch config dag to first task
                    first_edge = {
                        "from_task_reference": {
                            "kind": "app_task",
                            "uuid": system_dag_task["child_tasks_local_reference_list"][
                                0
                            ]["uuid"],
                        },
                        "to_task_reference": {
                            "kind": "app_task",
                            "name": user_first_task_name,
                            "uuid": cur_profile_task_name_uuid_map[config_name][
                                user_first_task_name
                            ],
                        },
                    }

                    # remaining edges from first task to rest of tasks
                    user_task_edges = custom_task["attrs"]["edges"]
                    for edge in user_task_edges:
                        task_name = edge["from_task_reference"]["name"]
                        edge["from_task_reference"][
                            "uuid"
                        ] = cur_profile_task_name_uuid_map[config_name][task_name]
                        task_name = edge["to_task_reference"]["name"]
                        edge["to_task_reference"][
                            "uuid"
                        ] = cur_profile_task_name_uuid_map[config_name][task_name]
                    system_dag_task["attrs"]["edges"] = [first_edge]
                    system_dag_task["attrs"]["edges"].extend(user_task_edges)

            for task in system_tasks:
                # removing additional attributes
                task.pop("state", "")
                task.pop("message_list", "")

    # profile level counter
    profile_idx = 0

    # attaching updated patch runbook to patch runbook in spec
    for profile in resources.get("app_profile_list", []):
        # patch list counter
        idx = 0

        for patch_config in profile.get("patch_list", []):
            patch_config["runbook"] = app_profile_list[profile_idx]["patch_list"][idx][
                "runbook"
            ]
            idx += 1

        profile_idx += 1


def strip_uuids(upload_payload):
    """Strip UUIDs from upload payload"""

    if isinstance(upload_payload, dict):
        key_list = list(upload_payload.keys())
        for key in key_list:
            if key == "uuid":
                del upload_payload[key]

            # elif key == "icon_reference":
            #     continue

            else:
                strip_uuids(upload_payload[key])
    elif isinstance(upload_payload, list):
        for item in upload_payload:
            strip_uuids(item)


def is_ncm_enabled(client):
    """
    Checks if NCM is enabled for the given client.
    Args:
        client (object): The client object which contains the connection information.
    Returns:
        tuple: A tuple containing:
            - ncm_enabled (bool): True if NCM is enabled, False otherwise.
            - ncm_url (str or None): The URL of the NCM if enabled, None otherwise.

    """
    ncm_enabled = False
    ncm_url = None

    if isinstance(client.connection, MultiConnection):
        try:
            Obj = get_resource_api(
                "groups", getattr(client.connection, MULTICONNECT.PC_OBJ), dm_api=True
            )
        except Exception as e:
            LOG.error("Error while fetching NCM enablement: {}".format(e))
            return ncm_enabled, ncm_url
    else:
        try:
            Obj = get_resource_api("groups", client.connection, dm_api=True)
        except Exception as e:
            LOG.error("Error while fetching NCM enablement: {}".format(e))
            return ncm_enabled, ncm_url

    payload = deepcopy(MARKETPLACE.FETCH_APP_DETAILS_PAYLOAD)

    payload["filter"] += ";app_name=={}".format(MARKETPLACE.APP_NAME.NCM)

    res, err = Obj.create(payload)
    if err:
        click.echo("[Fail]")
        LOG.error("[{}] - {}".format(err["code"], err["error"]))

    result = json.loads(res.content)

    for group in result.get("group_results", []):
        for entity in group.get("entity_results", []):
            ncm_url = entity.get("app_url")
            ncm_enabled = True
            break

    return ncm_enabled, ncm_url


def fetch_host_port_from_url(url):
    """
    Extracts the host and port from a given URL.
    Args:
        url (str): The URL from which to extract the host and port.
    Returns:
        tuple: A tuple containing the host and port. If the port is not specified in the URL, it returns None for the port.
    Raises:
        SystemExit: If an error occurs while fetching the host and port from the URL.
    """

    try:
        parsed_url = urlparse(url)

        # Extract host and port info from URL
        host = parsed_url.hostname
        port = parsed_url.port
        return host, port

    except Exception as e:
        LOG.error(
            "An unexpected error occurred while fetching host and port from URL({}): {}".format(
                url, e
            )
        )
        sys.exit("Error while fetching host and port from URL: {}".format(url))


def replace_host_port_in_url(url, new_host, new_port=None):
    """
    Replaces the host and optionally the port in the given URL.
    Args:
        url (str): The original URL.
        host (str): The new host to replace in the URL.
        port (str, optional): The new port to replace in the URL. If not provided, the original port is retained.
    Returns:
        str: The updated URL with the new host and port.
    Raises:
        SystemExit: If an unexpected error occurs during URL processing.
    """

    try:
        parsed_url = urlparse(url)
        old_port = parsed_url.port

        # if host and port are None, return the original URL
        if not (new_host and new_port):
            LOG.debug(
                "Returning original URL: {} as host: {} port: {}".format(
                    url, new_host, new_port
                )
            )
            return url

        # Replace host in the parsed URL
        updated_netloc = new_host

        # if port is given then update the netloc with port
        if new_port:
            updated_netloc += f":{new_port}"
        else:
            updated_netloc += f":{old_port}"

        # Construct the updated URL
        updated_url = parsed_url._replace(netloc=updated_netloc).geturl()

        return updated_url

    except Exception as e:
        LOG.error(
            "An unexpected error occurred while replacing host and port in URL({}): {}".format(
                url, e
            )
        )
        sys.exit("Error while replacing host and port in URL: {}".format(url))


def is_policy_check_required():
    """This helper returns whether policy enablement check is required for a setup"""

    context = get_context()
    ncm_server_config = context.get_ncm_server_config()
    NCM_ENABLED = ncm_server_config.get("ncm_enabled", False)

    if NCM_ENABLED:
        if FLAGS.POLICY_ON_SMSP:
            return False
        else:
            return True
    return True
