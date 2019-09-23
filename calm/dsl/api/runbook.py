from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_secrets, patch_secrets


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
        self.RUNLOG_LIST = self.PREFIX + "/runlogs/{}/childrens/list"
        self.RUNLOG_OUTPUT = self.PREFIX + "/runlogs/{}/childrens/{}/output"
        self.RUNLOG_RESUME = self.PREFIX + "/runlogs/{}/childrens/{}/resume"

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

    def update2(self, uuid, payload):
        return self.connection._call(
            self.UPDATE2.format(uuid), verify=False, request_json=payload, method=REQUEST.METHOD.PUT
        )

    @staticmethod
    def _make_runbook_payload(runbook_name, runbook_desc, runbook_resources, project_ref=None, spec_version=None):

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

        if project_ref:
            runbook_payload['metadata']['project_reference'] = project_ref

        return runbook_payload

    def upload_with_secrets(self, runbook_name, runbook_desc, runbook_resources, project_ref=None):

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
        object_lists = ["substrate_definition_list"]
        objects = ["runbook"]

        strip_secrets(runbook_resources, secret_map, secret_variables, object_lists=object_lists, objects=objects)

        upload_payload = self._make_runbook_payload(runbook_name, runbook_desc, runbook_resources, project_ref=project_ref)

        res, err = self.upload(upload_payload)

        if err:
            return res, err

        # Add secrets and update bp
        runbook = res.json()
        del runbook["status"]

        # Update blueprint
        update_payload = patch_secrets(runbook, secret_map, secret_variables)
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

    def update_with_secrets(self, uuid, runbook_name, runbook_desc, runbook_resources, spec_version, project_ref):

        secret_map = {}
        secret_variables = []
        object_lists = ["substrate_definition_list"]
        objects = ["runbook"]
        strip_secrets(runbook_resources, secret_map, secret_variables, object_lists=object_lists, objects=objects)

        update_payload = self._make_runbook_payload(runbook_name, runbook_desc, runbook_resources, project_ref=project_ref, spec_version=spec_version)
        update_payload["metadata"]["uuid"] = uuid

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
