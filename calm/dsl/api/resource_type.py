from .resource import ResourceAPI
from .connection import REQUEST


class ResourceTypeAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="resource_types", calm_api=True)
        self.CREATE = self.PREFIX
        self.TEST_RUNBOOK = self.PREFIX + "/{}/test_runbook/{}/run"
        self.UPDATE = self.PREFIX + "/{}"

    def create(self, resource_type_payload):
        return self.connection._call(
            self.CREATE,
            verify=False,
            request_json=resource_type_payload,
            method=REQUEST.METHOD.POST,
            timeout=(5, 300),
        )

    def update(self, uuid, resource_type_payload):
        return self.connection._call(
            self.UPDATE.format(uuid),
            verify=False,
            request_json=resource_type_payload,
            method=REQUEST.METHOD.PUT,
        )

    def run_test_runbook(self, resource_type_id, action_id, payload):
        return self.connection._call(
            self.TEST_RUNBOOK.format(resource_type_id, action_id),
            request_json=payload,
            verify=False,
            method=REQUEST.METHOD.POST,
        )
