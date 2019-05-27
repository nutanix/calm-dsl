from .resource import ResourceAPI
from .connection import REQUEST


class ApplicationAPI(ResourceAPI):

    PREFIX = ResourceAPI.PREFIX + "apps"
    LIST = PREFIX + "/list"
    ITEM = PREFIX + "/{}"
    ACTION_RUN = PREFIX + "/{}/actions/{}/run"

    def run_action(self, app_id, action_id, payload):
        return self.connection._call(
            self.ACTION_RUN.format(app_id, action_id),
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
