def strip_secrets(resources, secret_map, secret_variables, object_lists=[], objects=[]):
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
    default_creds = []
    for cred in creds:
        name = cred["name"]
        secret_map[name] = cred.pop("secret", {})
        # Explicitly set defaults so that secret is not created at server
        # TODO - Fix bug in server: {} != None
        cred["secret"] = {
            "attrs": {"is_secret_modified": False, "secret_reference": None}
        }
        if cred.pop("default"):
            default_creds.append(cred)
    """
    if not default_creds:
        raise ValueError("No default cred provided")
    if len(default_creds) > 1:
        raise ValueError(
            "Found more than one credential marked as default - {}".format(
                ", ".join(cred["name"] for cred in default_creds)
            )
        )
    """
    if default_creds:
        resources["default_credential_local_reference"] = {
            "kind": "app_credential",
            "name": default_creds[0]["name"] if default_creds else cred[0]["name"],
        }

    # Remove creds from HTTP endpoints resources
    auth = resources.get("authentication", {}) or {}
    if auth.get("type", None) == "basic":
        name = auth["username"]
        secret_map[name] = auth.pop("password", {})
        auth["password"] = {"attrs": {"is_secret_modified": False, "value": None}}

    # Strip secret variable values
    # TODO: Refactor and/or clean this up later

    def strip_entity_secret_variables(path_list, obj, field_name="variable_list"):
        for var_idx, variable in enumerate(obj.get(field_name, []) or []):
            if variable["type"] == "SECRET":
                secret_variables.append(
                    (path_list + [field_name, var_idx], variable.pop("value"))
                )
                variable["attrs"] = {
                    "is_secret_modified": False,
                    "secret_reference": None,
                }

    def strip_action_secret_variables(path_list, obj):
        for action_idx, action in enumerate(obj.get("action_list", []) or []):
            runbook = action.get("runbook", {}) or {}
            if not runbook:
                return
            strip_entity_secret_variables(
                path_list + ["action_list", action_idx, "runbook"], runbook
            )
            tasks = runbook.get("task_definition_list", [])
            for task_idx, task in enumerate(tasks):
                if task.get("type", None) != "HTTP":
                    continue
                auth = (task.get("attrs", {}) or {}).get("authentication", {}) or {}
                if auth.get("auth_type", None) == "basic":
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
                        )
                    )
                    auth["basic_auth"]["password"] = {
                        "attrs": {"is_secret_modified": False, "secret_reference": None}
                    }
                    if not (task.get("attrs", {}) or {}).get("headers", []) or []:
                        continue
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
                    )

    def strip_runbook_secret_variables(path_list, obj):
        tasks = obj.get("task_definition_list", [])
        for task_idx, task in enumerate(tasks):
            if task.get("type", None) != "HTTP":
                continue
            auth = (task.get("attrs", {}) or {}).get("authentication", {}) or {}
            path_list = path_list + [
                "runbook",
                "task_definition_list",
                task_idx,
                "attrs",
            ]
            strip_authentication_secret_variables(
                path_list, task.get("attrs", {}) or {}
            )
            if auth.get("auth_type", None) == "basic":
                if not (task.get("attrs", {}) or {}).get("headers", []) or []:
                    continue
                strip_entity_secret_variables(
                    path_list, task["attrs"], field_name="headers"
                )

    def strip_authentication_secret_variables(path_list, obj):
        auth = obj.get("authentication", {})
        if auth.get("auth_type", None) == "basic":
            secret_variables.append(
                (
                    path_list + ["authentication", "basic_auth", "password"],
                    auth["password"].pop("value"),
                )
            )
            auth["password"] = {"attrs": {"is_secret_modified": False}}

    def strip_all_secret_variables(path_list, obj):
        strip_entity_secret_variables(path_list, obj)
        strip_action_secret_variables(path_list, obj)
        strip_runbook_secret_variables(path_list, obj)
        strip_authentication_secret_variables(path_list, obj)

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


def patch_secrets(resources, secret_map, secret_variables):
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
        cred["secret"] = secret_map[name]

    # Add creds back for HTTP endpoint
    auth = resources.get("authentication", {})
    username = auth.get("username", "")
    if username:
        auth["password"] = secret_map[username]

    for path, secret in secret_variables:
        variable = resources
        for sub_path in path:
            variable = variable[sub_path]
        variable["attrs"] = {"is_secret_modified": True}
        variable["value"] = secret

    return resources
