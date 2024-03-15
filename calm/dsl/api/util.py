import copy

from calm.dsl.log import get_logging_handle

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
    creds = resources.get("credential_definition_list", []) or []
    filtered_decompiled_secret_credentials = get_secrets_from_context(
        decompiled_secrets, "credential_definition_list"
    )

    default_creds = []
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

    filtered_decompiled_secret_auth_creds = get_secrets_from_context(
        decompiled_secrets, "authentication"
    )

    # Remove creds from HTTP endpoints resources
    auth = resources.get("authentication", {}) or {}
    if auth.get("type", None) == "basic":
        if is_secret_modified(
            filtered_decompiled_secret_auth_creds, auth["username"], auth["password"]
        ):
            name = auth["username"]
            secret_map[name] = auth.pop("password", {})
            auth["password"] = {"attrs": {"is_secret_modified": False, "value": None}}

    # Strip secret variable values
    # TODO: Refactor and/or clean this up later

    def strip_entity_secret_variables(
        path_list, obj, field_name="variable_list", context=""
    ):

        if field_name != "headers" and obj.get("name", None):
            context = context + "." + obj["name"] + "." + field_name

        filtered_decompiled_secrets = get_secrets_from_context(
            decompiled_secrets, context
        )

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

    def strip_action_secret_variables(path_list, obj):

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
                        auth.get("basic_auth", {})
                        .get("password", {})
                        .get("value", None),
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

                http_task_headers = (task.get("attrs", {}) or {}).get(
                    "headers", []
                ) or []
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
                        field_name="headers",
                        context=var_runbook_task_name_context + ".headers",
                    )

    def strip_runbook_secret_variables(path_list, obj):

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
                    path_list, task["attrs"], field_name="inarg_list"
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
                path_list, task.get("attrs", {}) or {}, context=var_task_context
            )

            if not (task.get("attrs", {}) or {}).get("headers", []) or []:
                continue
            strip_entity_secret_variables(
                path_list,
                task["attrs"],
                field_name="headers",
                context=var_task_context + ".headers",
            )

    def strip_authentication_secret_variables(path_list, obj, context=""):

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

    def strip_all_secret_variables(path_list, obj):
        strip_entity_secret_variables(path_list, obj, context=path_list[0])
        strip_action_secret_variables(path_list, obj)
        strip_runbook_secret_variables(path_list, obj)
        strip_authentication_secret_variables(path_list, obj, context=path_list[0])

    for object_list in object_lists:
        for obj_idx, obj in enumerate(resources.get(object_list, []) or []):
            strip_all_secret_variables([object_list, obj_idx], obj)

            # Currently, deployment actions and variables are unsupported.
            # Uncomment the following lines if and when the API does support them.
            # if object_list == "app_profile_list":
            #     for dep_idx, dep in enumerate(obj["deployment_create_list"]):
            #         strip_all_secret_variables(
            #             [object_list, obj_idx, "deployment_create_list", dep_idx],
            #             dep,
            #         )

    for obj in objects:
        strip_all_secret_variables([obj], resources.get(obj, {}))


# Handling vmware secrets
def strip_vmware_secrets(
    path_list, obj, secret_variables=[], decompiled_secrets=[], not_stripped_secrets=[]
):
    path_list.extend(["create_spec", "resources", "guest_customization"])
    obj = obj["create_spec"]["resources"]["guest_customization"]
    vmware_secrets_context = "create_spec.resources.guest_customization.windows_data"

    if "windows_data" in obj:
        path_list.append("windows_data")
        obj = obj["windows_data"]
        vmware_secrets_admin_context = (
            vmware_secrets_context
            + obj["windows_data"]
            + ".password."
            + obj["password"]["name"]
        )
        filtered_decompiled_vmware_secrets = get_secrets_from_context(
            decompiled_secrets, vmware_secrets_admin_context
        )

        # Check for admin_password
        if "password" in obj:
            if is_secret_modified(
                filtered_decompiled_vmware_secrets,
                obj["password"]["name"],
                obj["password"]["value"],
            ):
                secret_variables.append(
                    (
                        path_list + ["password"],
                        obj["password"].pop("value", ""),
                        obj["password"]["name"],
                    )
                )
                obj["password"]["attrs"] = {
                    "is_secret_modified": False,
                    "secret_reference": None,
                }
            else:
                not_stripped_secrets.append(
                    (path_list + ["password"], obj["password"]["value"])
                )

        vmware_secrets_domain_context = (
            vmware_secrets_context
            + obj["windows_data"]
            + ".domain_password."
            + obj["domain_password"]
        )
        filtered_decompiled_vmware_secrets = get_secrets_from_context(
            decompiled_secrets, vmware_secrets_domain_context
        )

        # Now check for domain password
        if obj.get("is_domain", False):
            if "domain_password" in obj:
                if is_secret_modified(
                    filtered_decompiled_vmware_secrets,
                    obj["domain_password"]["name"],
                    obj["domain_password"]["value"],
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
    entity_type_list = ["service_definition_list", "app_profile_list"]
    for entity_type in entity_type_list:
        _create_task_name_substrate_map(bp_payload, entity_type, **kwargs)

    for entity_type in entity_type_list:
        _create_reference_runbook_substrate_map(
            exported_bp_payload, entity_type, **kwargs
        )

    return reference_runbook_to_substrate_map
