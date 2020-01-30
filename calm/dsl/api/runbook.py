from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_secrets, patch_secrets
from calm.dsl.config import get_config
from .project import ProjectAPI


class RunbookAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="runbooks")
        self.UPLOAD = self.PREFIX + "/import_json"
        self.UPDATE2 = self.PREFIX + "/{}/update"
        self.PREVIOUS_RUNS = self.PREFIX + "/runlogs/list"
        self.RUN = self.PREFIX + "/{}/run"
        self.POLL_RUN = self.PREFIX + "/runlogs/{}"
        self.PAUSE = self.PREFIX + "/runlogs/{}/pause"
        self.PLAY = self.PREFIX + "/runlogs/{}/play"
        self.RERUN = self.PREFIX + "/runlogs/{}/rerun"
        self.RUNLOG_LIST = self.PREFIX + "/runlogs/{}/children/list"
        self.RUNLOG_OUTPUT = self.PREFIX + "/runlogs/{}/children/{}/output"
        self.RUNLOG_RESUME = self.PREFIX + "/runlogs/{}/children/{}/resume"
        self.RUNLOG_ABORT = self.PREFIX + "/runlogs/{}/abort"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def resume(self, arlid, trlid, payload):
        return self.connection._call(
            self.RUNLOG_RESUME.format(arlid, trlid), verify=False, request_json=payload, method=REQUEST.METHOD.POST
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

    def abort(self, uuid):
        return self.connection._call(
            self.RUNLOG_ABORT.format(uuid), verify=False, request_json={}, method=REQUEST.METHOD.POST
        )

    def update2(self, uuid, payload):
        return self.connection._call(
            self.UPDATE2.format(uuid), verify=False, request_json=payload, method=REQUEST.METHOD.PUT
        )

    @staticmethod
    def _make_runbook_payload(runbook_name, runbook_desc, runbook_resources, spec_version=None):

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
            "api_version": "3.0"
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
                err = {"error": err_msg, "code": -1}
                return None, err

        secret_map = {}
        secret_variables = []
        object_lists = []
        objects = ["runbook"]

        strip_secrets(runbook_resources, secret_map, secret_variables, object_lists=object_lists, objects=objects)

        endpoint_secret_map = {}
        endpoint_secret_variables = {}

        for endpoint in runbook_resources.get("endpoint_definition_list"):
            endpoint_name = endpoint.get("name")
            endpoint_secret_map[endpoint_name] = {}
            endpoint_secret_variables[endpoint_name] = []
            strip_secrets(endpoint["attrs"], endpoint_secret_map[endpoint_name], endpoint_secret_variables[endpoint_name])
            endpoint["attrs"].pop("default_credential_local_reference", None)

        upload_payload = self._make_runbook_payload(runbook_name, runbook_desc, runbook_resources)

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
        runbook = res.json()
        del runbook["status"]

        # Update blueprint
        patch_secrets(runbook['spec']['resources'], secret_map, secret_variables)
        for endpoint in runbook['spec']['resources'].get('endpoint_definition_list', []):
            endpoint_name = endpoint.get("name")
            patch_secrets(endpoint["attrs"], endpoint_secret_map[endpoint_name], endpoint_secret_variables[endpoint_name])

        uuid = runbook["metadata"]["uuid"]

        return self.update(uuid, runbook)

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

        secret_map = {}
        secret_variables = []
        object_lists = ["substrate_definition_list"]
        objects = ["runbook"]
        strip_secrets(runbook_resources, secret_map, secret_variables, object_lists=object_lists, objects=objects)

        update_payload = self._make_runbook_payload(runbook_name, runbook_desc, runbook_resources, spec_version=spec_version)
        update_payload["metadata"]["uuid"] = uuid

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
        update_payload["metadata"]["project_reference"] = {
            "kind": "project",
            "uuid": project_id,
            "name": project_name,
        }

        res, err = self.update2(uuid, update_payload)

        if err:
            return res, err

        # Add secrets and update bp
        runbook = res.json()
        del runbook["status"]

        # Update blueprint
        update_payload = patch_secrets(runbook, secret_map, secret_variables)
        uuid = runbook["metadata"]["uuid"]

        return self.update(uuid, update_payload)
