from .connection import REQUEST
from .entity import EntityAPI


class ApplicationAPI(EntityAPI):

    APP_PREFIX = EntityAPI.PREFIX + "apps"
    APP_LIST = APP_PREFIX + "/list"
    APP_ITEM = APP_PREFIX + "/{}"
    ACTION_RUN = APP_PREFIX + "/{}/actions/{}/run"

    def list(self, params=None):
        return self.connection._call(
            ApplicationAPI.APP_LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
        )

    def get(self, app_id):
        return self.connection._call(
            ApplicationAPI.APP_ITEM.format(app_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def run_action(self, app_id, action_id, payload):
        return self.connection._call(
            ApplicationAPI.ACTION_RUN.format(app_id, action_id),
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
        delete_url = ApplicationAPI.APP_ITEM.format(app_id)
        if soft_delete:
            delete_url += "?type=soft"
        return self.connection._call(
            delete_url, verify=False, method=REQUEST.METHOD.DELETE
        )
