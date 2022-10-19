from .resource import ResourceAPI
from .connection import REQUEST


class PolicyAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="policies")
        self.POLICY_EXECUTION_LIST = self.PREFIX + "/{}/executions/list"
        self.POLICY_EXECUTION = self.PREFIX + "/{}/executions/{}"

    def list_policy_execution(self, uuid, params=None):
        return self.connection._call(
            self.POLICY_EXECUTION_LIST.format(uuid),
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
        )

    def get_policy_execution(self, uuid, exec_uuid):
        return self.connection._call(
            self.POLICY_EXECUTION.format(uuid, exec_uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.GET,
        )
