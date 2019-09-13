from .resource import ResourceAPI
from .connection import REQUEST


class RunbookAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="actions")
        self.UPLOAD = self.PREFIX + "/import_json"
        self.UPDATE2 = self.PREFIX + "/{}/update"
        self.PREVIOUS_RUNS = self.PREFIX + "/runlogs/list"
        self.RUN = self.PREFIX + "/{}/run"
        self.POLL_RUN = self.PREFIX + "/runlogs/{}"
        self.PAUSE = self.PREFIX + "/runlogs/{}/pause"
        self.PLAY = self.PREFIX + "/runlogs/{}/play"
        self.RERUN = self.PREFIX + "/runlogs/{}/rerun"
        self.RUNLOG_LIST = self.PREFIX + "/runlogs/{}/list"
        self.RUNLOG_OUTPUT = self.PREFIX + "/{}/runlogs/{}/output"
        self.RUNLOG_RESUME = self.PREFIX + "/runlogs/{}/resume"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def resume(self, uuid, payload):
        return self.connection._call(
            self.RUNLOG_RESUME.format(uuid), verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def pause(self, uuid):
        return self.connection._call(
            self.PAUSE.format(uuid), verify=False, request_json={}, method=REQUEST.METHOD.POST
        )

    def play(self, uuid):
        return self.connection._call(
            self.PLAY.format(uuid), verify=False, request_json={}, method=REQUEST.METHOD.POST
        )

    def rerun(self, uuid):
        return self.connection._call(
            self.RERUN.format(uuid), verify=False, request_json={}, method=REQUEST.METHOD.POST
        )

    def update2(self, uuid, payload):
        return self.connection._call(
            self.UPDATE2.format(uuid), verify=False, request_json=payload, method=REQUEST.METHOD.PUT
        )

    @staticmethod
    def _make_runbook_payload(runbook_name, runbook_desc, runbook_resources):

        runbook_payload = {
            "spec": {
                "name": runbook_name,
                "description": runbook_desc or "",
                "resources": runbook_resources,
            },
            "metadata": {"spec_version": 1, "name": runbook_name, "kind": "action"},
            "api_version": "3.0",
        }

        return runbook_payload

    def upload_with_secrets(self, runbook_name, runbook_desc, runbook_resources):

        # check if runbook with the given name already exists
        params = {"filter": "name=={};deleted==FALSE".format(runbook_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)
        if entities:
            if len(entities) > 0:
                err_msg = "Runbook with name {} already exists.".format(runbook_name)
                # ToDo: Add command to edit Blueprints
                err = {"error": err_msg, "code": -1}
                return None, err

        # Remove creds before upload
        creds = runbook_resources.get("credential_definition_list", []) or []
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
            runbook_resources["default_credential_local_reference"] = {
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

        def strip_runbook_secret_variables(path_list, obj):
            tasks = obj.get("task_definition_list", [])
            for task_idx, task in enumerate(tasks):
                if task.get("type", None) != "HTTP":
                    continue
                auth = (task.get("attrs", {}) or {}).get("authentication", {}) or {}
                if auth.get("auth_type", None) == "basic":
                    secret_variables.append(
                        (
                            path_list
                            + [
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
            strip_runbook_secret_variables(path_list, obj)

        object_lists = [
            "substrate_definition_list",
        ]
        for object_list in object_lists:
            for obj_idx, obj in enumerate(runbook_resources.get(object_list, []) or []):
                strip_all_secret_variables([object_list, obj_idx], obj)

        strip_entity_secret_variables(["runbook"], runbook_resources.get("runbook", {}))
        strip_runbook_secret_variables(["runbook"], runbook_resources.get("runbook", {}))

        upload_payload = self._make_runbook_payload(runbook_name, runbook_desc, runbook_resources)

        res, err = self.upload(upload_payload)

        if err:
            return res, err

        # Add secrets and update bp
        runbook = res.json()
        del runbook["status"]

        # Add secrets back
        creds = runbook["spec"]["resources"]["credential_definition_list"]
        for cred in creds:
            name = cred["name"]
            cred["secret"] = secret_map[name]

        for path, secret in secret_variables:
            variable = runbook["spec"]["resources"]
            for sub_path in path:
                variable = variable[sub_path]
            variable["attrs"] = {"is_secret_modified": True}
            variable["value"] = secret

        # Update blueprint
        update_payload = runbook
        uuid = runbook["metadata"]["uuid"]

        return self.update(uuid, update_payload)

    def list_previous_runs(self, params=None):
        return self.connection._call(
            self.PREVIOUS_RUNS, verify=False, request_json=params, method=REQUEST.METHOD.POST
        )

    def run(self, uuid, payload):
        return self.connection._call(
            self.RUN.format(uuid), verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def list_runlogs(self, uuid):
        return self.connection._call(
            self.RUNLOG_LIST.format(uuid), verify=False, request_json={}, method=REQUEST.METHOD.POST
        )

    def runlog_output(self, arl_id, trl_id):
        return self.connection._call(
            self.RUNLOG_OUTPUT.format(arl_id, trl_id), verify=False, method=REQUEST.METHOD.GET
        )

    def poll_action_run(self, uuid, payload=None):
        if payload:
            return self.connection._call(
                self.POLL_RUN.format(uuid), request_json=payload, verify=False, method=REQUEST.METHOD.POST
            )
        else:
            return self.connection._call(
                self.POLL_RUN.format(uuid), verify=False, method=REQUEST.METHOD.GET
            )

    def update_with_secrets(self, uuid, runbook_name, runbook_desc, runbook_resources, spec_version):

        # Remove creds before upload
        creds = runbook_resources.get("credential_definition_list", []) or []
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
            runbook_resources["default_credential_local_reference"] = {
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

        def strip_runbook_secret_variables(path_list, obj):
            tasks = obj.get("task_definition_list", [])
            for task_idx, task in enumerate(tasks):
                if task.get("type", None) != "HTTP":
                    continue
                auth = (task.get("attrs", {}) or {}).get("authentication", {}) or {}
                if auth.get("auth_type", None) == "basic":
                    secret_variables.append(
                        (
                            path_list
                            + [
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
            strip_runbook_secret_variables(path_list, obj)

        object_lists = [
            "substrate_definition_list",
        ]
        for object_list in object_lists:
            for obj_idx, obj in enumerate(runbook_resources.get(object_list, []) or []):
                strip_all_secret_variables([object_list, obj_idx], obj)

        strip_entity_secret_variables(["runbook"], runbook_resources.get("runbook", {}))
        strip_runbook_secret_variables(["runbook"], runbook_resources.get("runbook", {}))

        update_payload = self._make_runbook_payload(runbook_name, runbook_desc, runbook_resources)
        update_payload["metadata"]["uuid"] = uuid
        update_payload["metadata"]["spec_version"] = spec_version

        res, err = self.update2(uuid, update_payload)

        if err:
            return res, err

        # Add secrets and update bp
        runbook = res.json()
        del runbook["status"]

        # Add secrets back
        creds = runbook["spec"]["resources"]["credential_definition_list"]
        for cred in creds:
            name = cred["name"]
            cred["secret"] = secret_map[name]

        for path, secret in secret_variables:
            variable = runbook["spec"]["resources"]
            for sub_path in path:
                variable = variable[sub_path]
            variable["attrs"] = {"is_secret_modified": True}
            variable["value"] = secret

        # Update blueprint
        update_payload = runbook
        uuid = runbook["metadata"]["uuid"]

        return self.update(uuid, update_payload)
