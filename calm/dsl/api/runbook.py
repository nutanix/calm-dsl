import os

from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_secrets, patch_secrets
from calm.dsl.config import get_context
from .project import ProjectAPI


class RunbookAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="runbooks")
        self.UPLOAD = self.PREFIX + "/import_json"
        self.UPDATE_USING_NAMES = self.PREFIX + "/{}/update"
        self.RUNBOOK_RUNLOGS_LIST = self.PREFIX + "/runlogs/list"
        self.RUN = self.PREFIX + "/{}/run"
        self.POLL_RUN = self.PREFIX + "/runlogs/{}"
        self.PAUSE = self.PREFIX + "/runlogs/{}/pause"
        self.PLAY = self.PREFIX + "/runlogs/{}/play"
        self.RERUN = self.PREFIX + "/runlogs/{}/rerun"
        self.RUNLOG_LIST = self.PREFIX + "/runlogs/{}/children/list"
        self.RUNLOG_OUTPUT = self.PREFIX + "/runlogs/{}/children/{}/output"
        self.RUNLOG_RESUME = self.PREFIX + "/runlogs/{}/children/{}/resume"
        self.RUNLOG_ABORT = self.PREFIX + "/runlogs/{}/abort"
        self.RUN_SCRIPT = self.PREFIX + "/{}/run_script"
        self.RUN_SCRIPT_OUTPUT = self.PREFIX + "/{}/run_script/output/{}/{}"
        self.EXPORT_FILE = self.ITEM + "/export_file"
        self.IMPORT_FILE = self.PREFIX + "/import_file"
        self.EXPORT_JSON = self.ITEM + "/export_json"
        self.EXPORT_JSON_WITH_SECRETS = self.ITEM + "/export_json?keep_secrets=true"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def resume(self, action_runlog_id, task_runlog_id, payload):
        return self.connection._call(
            self.RUNLOG_RESUME.format(action_runlog_id, task_runlog_id),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def pause(self, uuid):
        return self.connection._call(
            self.PAUSE.format(uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.POST,
        )

    def play(self, uuid):
        return self.connection._call(
            self.PLAY.format(uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.POST,
        )

    def rerun(self, uuid):
        return self.connection._call(
            self.RERUN.format(uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.POST,
        )

    def abort(self, uuid):
        return self.connection._call(
            self.RUNLOG_ABORT.format(uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.POST,
        )

    def update_using_name_reference(self, uuid, payload):
        return self.connection._call(
            self.UPDATE_USING_NAMES.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    @staticmethod
    def _make_runbook_payload(
        runbook_name, runbook_desc, runbook_resources, spec_version=None
    ):

        runbook_payload = {
            "spec": {
                "name": runbook_name,
                "description": runbook_desc or "",
                "resources": runbook_resources,
            },
            "metadata": {
                "spec_version": spec_version or 1,
                "name": runbook_name,
                "kind": "runbook",
            },
            "api_version": "3.0",
        }

        return runbook_payload

    def upload_with_secrets(
        self, runbook_name, runbook_desc, runbook_resources, force_create=False
    ):

        # check if runbook with the given name already exists
        params = {"filter": "name=={};deleted==FALSE".format(runbook_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)
        if entities:
            if len(entities) > 0:
                if not force_create:
                    err_msg = "Runbook {} already exists. Use --force to first delete existing runbook before create.".format(
                        runbook_name
                    )
                    err = {"error": err_msg, "code": -1}
                    return None, err

                # --force option used in create. Delete existing runbook with same name.
                rb_uuid = entities[0]["metadata"]["uuid"]
                _, err = self.delete(rb_uuid)
                if err:
                    return None, err

        secret_map = {}
        secret_variables = []
        object_lists = []
        objects = ["runbook"]

        strip_secrets(
            runbook_resources,
            secret_map,
            secret_variables,
            object_lists=object_lists,
            objects=objects,
        )

        endpoint_secret_map = {}
        endpoint_secret_variables = {}

        for endpoint in runbook_resources.get("endpoint_definition_list"):
            endpoint_name = endpoint.get("name")
            endpoint_secret_map[endpoint_name] = {}
            endpoint_secret_variables[endpoint_name] = []
            strip_secrets(
                endpoint["attrs"],
                endpoint_secret_map[endpoint_name],
                endpoint_secret_variables[endpoint_name],
            )
            endpoint["attrs"].pop("default_credential_local_reference", None)

        upload_payload = self._make_runbook_payload(
            runbook_name, runbook_desc, runbook_resources
        )

        ContextObj = get_context()
        project_config = ContextObj.get_project_config()
        project_name = project_config["name"]
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

        runbook = res.json()
        del runbook["status"]

        # Add secrets and update runbook
        patch_secrets(runbook["spec"]["resources"], secret_map, secret_variables)
        for endpoint in runbook["spec"]["resources"].get(
            "endpoint_definition_list", []
        ):
            endpoint_name = endpoint.get("name")
            patch_secrets(
                endpoint["attrs"],
                endpoint_secret_map[endpoint_name],
                endpoint_secret_variables[endpoint_name],
            )

        uuid = runbook["metadata"]["uuid"]

        # Update runbook
        return self.update(uuid, runbook)

    def list_runbook_runlogs(self, params=None):
        return self.connection._call(
            self.RUNBOOK_RUNLOGS_LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
        )

    def run(self, uuid, payload):
        return self.connection._call(
            self.RUN.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def run_script(self, uuid, payload):
        return self.connection._call(
            self.RUN_SCRIPT.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def run_script_output(self, uuid, trl_id, request_id):
        return self.connection._call(
            self.RUN_SCRIPT_OUTPUT.format(uuid, trl_id, request_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def list_runlogs(self, uuid):
        return self.connection._call(
            self.RUNLOG_LIST.format(uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.POST,
        )

    def runlog_output(self, action_runlog_id, task_runlog_id):
        return self.connection._call(
            self.RUNLOG_OUTPUT.format(action_runlog_id, task_runlog_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def poll_action_run(self, uuid, payload=None):
        if payload:
            return self.connection._call(
                self.POLL_RUN.format(uuid),
                request_json=payload,
                verify=False,
                method=REQUEST.METHOD.POST,
            )
        else:
            return self.connection._call(
                self.POLL_RUN.format(uuid), verify=False, method=REQUEST.METHOD.GET
            )

    def update_with_secrets(
        self, uuid, runbook_name, runbook_desc, runbook_resources, spec_version
    ):

        secret_map = {}
        secret_variables = []
        object_lists = []
        objects = ["runbook"]

        strip_secrets(
            runbook_resources,
            secret_map,
            secret_variables,
            object_lists=object_lists,
            objects=objects,
        )

        endpoint_secret_map = {}
        endpoint_secret_variables = {}

        for endpoint in runbook_resources.get("endpoint_definition_list"):
            endpoint_name = endpoint.get("name")
            endpoint_secret_map[endpoint_name] = {}
            endpoint_secret_variables[endpoint_name] = []
            strip_secrets(
                endpoint["attrs"],
                endpoint_secret_map[endpoint_name],
                endpoint_secret_variables[endpoint_name],
            )
            endpoint["attrs"].pop("default_credential_local_reference", None)

        update_payload = self._make_runbook_payload(
            runbook_name, runbook_desc, runbook_resources, spec_version=spec_version
        )

        ContextObj = get_context()
        project_config = ContextObj.get_project_config()
        project_name = project_config["name"]
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
        update_payload["metadata"]["project_reference"] = {
            "kind": "project",
            "uuid": project_id,
            "name": project_name,
        }

        res, err = self.update_using_name_reference(uuid, update_payload)
        if err:
            return res, err

        # Add secrets and update runbook
        runbook = res.json()
        del runbook["status"]

        # Update runbook
        patch_secrets(runbook["spec"]["resources"], secret_map, secret_variables)
        for endpoint in runbook["spec"]["resources"].get(
            "endpoint_definition_list", []
        ):
            endpoint_name = endpoint.get("name")
            patch_secrets(
                endpoint["attrs"],
                endpoint_secret_map[endpoint_name],
                endpoint_secret_variables[endpoint_name],
            )

        uuid = runbook["metadata"]["uuid"]

        return self.update(uuid, runbook)

    def export_file(self, uuid, passphrase=None):
        current_path = os.path.dirname(os.path.realpath(__file__))
        if passphrase:
            res, err = self.connection._call(
                self.EXPORT_FILE.format(uuid),
                verify=False,
                method=REQUEST.METHOD.POST,
                request_json={"passphrase": passphrase},
                files=[],
            )
        else:
            res, err = self.connection._call(
                self.EXPORT_FILE.format(uuid), verify=False, method=REQUEST.METHOD.GET
            )

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        with open(current_path + "/" + uuid + ".json", "wb") as downloaded_file:
            for chunk in res.iter_content(chunk_size=2048):
                downloaded_file.write(chunk)

        return current_path + "/" + uuid + ".json"

    def import_file(self, file_path, name, project_uuid, passphrase=None):

        payload = {"name": name, "project_uuid": project_uuid}
        if passphrase:
            payload["passphrase"] = passphrase
        files = {"file": ("file", open(file_path, "rb"))}

        return self.connection._call(
            self.IMPORT_FILE,
            verify=False,
            files=files,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def export_json(self, uuid):
        url = self.EXPORT_JSON.format(uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def export_json_with_secrets(self, uuid):
        url = self.EXPORT_JSON_WITH_SECRETS.format(uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)
