from .resource import ResourceAPI
from .connection import REQUEST


class ResourceTypeAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="resource_types", calm_api=True)
        self.TEST_RUNBOOK = self.PREFIX + "/{}/test_runbook/{}/run"

    def run_test_runbook(self, resource_type_id, action_id, payload):
        return self.connection._call(
            self.TEST_RUNBOOK.format(resource_type_id, action_id),
            request_json=payload,
            verify=False,
            method=REQUEST.METHOD.POST,
        )
