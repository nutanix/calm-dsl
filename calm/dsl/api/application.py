from .resource import ResourceAPI
from .connection import REQUEST


class ApplicationAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="apps")

        self.ACTION_RUN = self.ITEM + "/actions/{}/run"
        self.PATCH_RUN = self.ITEM + "/patch/{}/run"
        self.DOWNLOAD_RUNLOG = self.ITEM + "/app_runlogs/{}/output/download"
        self.ACTION_VARIABLE = self.ITEM + "/actions/{}/variables"
        self.RECOVERY_GROUPS_LIST = self.ITEM + "/recovery_groups/list"

    def run_action(self, app_id, action_id, payload):
        return self.connection._call(
            self.ACTION_RUN.format(app_id, action_id),
            request_json=payload,
            verify=False,
            method=REQUEST.METHOD.POST,
        )

    def run_patch(self, app_id, patch_id, payload):
        return self.connection._call(
            self.PATCH_RUN.format(app_id, patch_id),
            request_json=payload,
            verify=False,
            method=REQUEST.METHOD.POST,
        )

    def poll_action_run(self, poll_url, payload=None):
        if payload:
            return self.connection._call(
                poll_url, request_json=payload, verify=False, method=REQUEST.METHOD.POST
            )
        else:
            return self.connection._call(
                poll_url, verify=False, method=REQUEST.METHOD.GET
            )

    def delete(self, app_id, soft_delete=False):
        delete_url = self.ITEM.format(app_id)
        if soft_delete:
            delete_url += "?type=soft"
        return self.connection._call(
            delete_url, verify=False, method=REQUEST.METHOD.DELETE
        )

    def download_runlog(self, app_id, runlog_id):
        download_url = self.DOWNLOAD_RUNLOG.format(app_id, runlog_id)
        return self.connection._call(
            download_url, method=REQUEST.METHOD.GET, verify=False
        )

    def action_variables(self, app_id, action_name):
        action_var_url = self.ACTION_VARIABLE.format(app_id, action_name)
        return self.connection._call(
            action_var_url, method=REQUEST.METHOD.GET, verify=False
        )

    def get_recovery_groups(self, app_id, api_filter, length=250, offset=0):
        payload = {"filter": api_filter, "length": length, "offset": offset}
        recovery_groups_url = self.RECOVERY_GROUPS_LIST.format(app_id)
        return self.connection._call(
            recovery_groups_url,
            request_json=payload,
            verify=False,
            method=REQUEST.METHOD.POST,
        )
