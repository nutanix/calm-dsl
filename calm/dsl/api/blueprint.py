from .resource import ResourceAPI
from .connection import REQUEST
from calm.dsl.config import get_config
from .project import ProjectAPI


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

        # Handling vmware secrets
        def strip_vmware_secrets(path_list, obj):
            path_list.extend(["create_spec", "resources", "guest_customization"])
            obj = obj["create_spec"]["resources"]["guest_customization"]

            if "windows_data" in obj:
                path_list.append("windows_data")
                obj = obj["windows_data"]

                # Check for admin_password
                if "password" in obj:
                    secret_variables.append(
                        (path_list + ["password"], obj["password"].pop("value", ""))
                    )
                    obj["password"]["attrs"] = {
                        "is_secret_modified": False,
                        "secret_reference": None,
                    }

                # Now check for domain password
                if obj.get("is_domain", False):
                    if "domain_password" in obj:
                        secret_variables.append(
                            (
                                path_list + ["domain_password"],
                                obj["domain_password"].pop("value", ""),
                            )
                        )
                        obj["domain_password"]["attrs"] = {
                            "is_secret_modified": False,
                            "secret_reference": None,
                        }

        for obj_index, obj in enumerate(bp_resources.get("substrate_definition_list", []) or []):
            if (obj["type"] == "VMWARE_VM") and (obj["os_type"] == "Windows"):
                strip_vmware_secrets(["substrate_definition_list", obj_index], obj)

        upload_payload = self._make_blueprint_payload(bp_name, bp_desc, bp_resources)

        config = get_config()
        project_name = config["PROJECT"]["name"]
        projectObj = ProjectAPI(self.connection)

        # Fetch project details
        params = {"filter": "name=={}".format(project_name)}
        res, err = projectObj.list(params=params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities", None)
        if not entities:
            raise Exception("No project with name {} exists".format(project_name))

        project_id = entities[0]["metadata"]["uuid"]

        # Setting project reference
        upload_payload["metadata"]["project_reference"] = {
            "kind": "project",
            "uuid": project_id,
            "name": project_name,
        }

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
        # Populating the categories at runtime
        config_categories = dict(config.items("CATEGORIES"))
        if categories:
            config_categories.update(categories)

        bp["metadata"]["categories"] = config_categories

        # Update blueprint
        update_payload = bp
        uuid = bp["metadata"]["uuid"]

        return self.update(uuid, update_payload)
