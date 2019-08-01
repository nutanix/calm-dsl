from .resource import ResourceAPI
from .connection import REQUEST


class BlueprintAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="blueprints")
        self.UPLOAD = self.PREFIX + "/import_json"
        self.LAUNCH = self.ITEM + "/simple_launch"
        self.FULL_LAUNCH = self.ITEM + "/launch"
        self.LAUNCH_POLL = self.ITEM + "/pending_launches/{}"
        self.BP_EDITABLES = self.ITEM + "/runtime_editables"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def launch(self, uuid, payload):
        return self.connection._call(
            self.LAUNCH.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def full_launch(self, uuid, payload):
        return self.connection._call(
            self.FULL_LAUNCH.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def poll_launch(self, blueprint_id, request_id):
        return self.connection._call(
            self.LAUNCH_POLL.format(blueprint_id, request_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def _get_editables(self, bp_uuid):
        return self.connection._call(
            self.BP_EDITABLES.format(bp_uuid), verify=False, method=REQUEST.METHOD.GET
        )

    @staticmethod
    def _make_blueprint_payload(bp_name, bp_desc, bp_resources, categories=None):

        bp_payload = {
            "spec": {
                "name": bp_name,
                "description": bp_desc or "",
                "resources": bp_resources,
            },
            "metadata": {"spec_version": 1, "name": bp_name, "kind": "blueprint"},
            "api_version": "3.0",
        }

        if categories:
            bp_payload["categories"] = categories

        return bp_payload

    def upload_with_secrets(self, bp_name, bp_desc, bp_resources, categories=None):

        # check if bp with the given name already exists
        params = {"filter": "name=={};state!=DELETED".format(bp_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)
        if entities:
            if len(entities) > 0:
                err_msg = "Blueprint with name {} already exists.".format(bp_name)
                # ToDo: Add command to edit Blueprints
                err = {"error": err_msg, "code": -1}
                return None, err

        # Remove creds before upload
        creds = bp_resources.get("credential_definition_list", []) or []
        secret_map = {}
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
            bp_resources["default_credential_local_reference"] = {
                "kind": "app_credential",
                "name": default_creds[0]["name"],
            }

        # Strip secret variable values
        # TODO: Refactor and/or clean this up later

        secret_variables = []

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

        def strip_action_secret_varaibles(path_list, obj):
            for action_idx, action in enumerate(obj.get("action_list", []) or []):
                runbook = action.get("runbook", {}) or {}
                if not runbook:
                    return
                strip_entity_secret_variables(
                    path_list + ["action_list", action_idx, "runbook"], runbook
                )
                tasks = runbook.get("task_definition_list", []) or []
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
                            "attrs": {
                                "is_secret_modified": False,
                                "secret_reference": None,
                            }
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

        def strip_all_secret_variables(path_list, obj):
            strip_entity_secret_variables(path_list, obj)
            strip_action_secret_varaibles(path_list, obj)

        object_lists = [
            "service_definition_list",
            "package_definition_list",
            "substrate_definition_list",
            "app_profile_list",
        ]
        for object_list in object_lists:
            for obj_idx, obj in enumerate(bp_resources.get(object_list, []) or []):
                strip_all_secret_variables([object_list, obj_idx], obj)

                # Currently, deployment actions and variables are unsupported.
                # Uncomment the following lines if and when the API does support them.
                # if object_list == "app_profile_list":
                #     for dep_idx, dep in enumerate(obj["deployment_create_list"]):
                #         strip_all_secret_variables(
                #             [object_list, obj_idx, "deployment_create_list", dep_idx],
                #             dep,
                #         )

        upload_payload = self._make_blueprint_payload(bp_name, bp_desc, bp_resources)

        res, err = self.upload(upload_payload)

        if err:
            return res, err

        # Add secrets and update bp
        bp = res.json()
        del bp["status"]

        # Add secrets back
        creds = bp["spec"]["resources"]["credential_definition_list"]
        for cred in creds:
            name = cred["name"]
            cred["secret"] = secret_map[name]

        for path, secret in secret_variables:
            variable = bp["spec"]["resources"]
            for sub_path in path:
                variable = variable[sub_path]
            variable["attrs"] = {"is_secret_modified": True}
            variable["value"] = secret

        # TODO - insert categories during update as /import_json fails if categories are given!
        if categories:
            bp["metadata"]["categories"] = categories

        # Update blueprint
        update_payload = bp
        uuid = bp["metadata"]["uuid"]

        return self.update(uuid, update_payload)
