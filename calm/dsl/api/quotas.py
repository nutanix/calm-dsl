from .resource import ResourceAPI
from .connection import REQUEST


class QuotasAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="quotas", calm_api=True)
        self.CREATE = self.PREFIX
        self.UPDATE_STATE = self.PREFIX + "/update/state"
        self.LIST = self.PREFIX + "/list"
        self.UPDATE = self.PREFIX + "/{}"

    def update_state(self, payload):
        return self.connection._call(
            self.UPDATE_STATE,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
            timeout=(5, 300),
        )

    def list(self, payload):
        return self.connection._call(
            self.LIST,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
            timeout=(5, 300),
        )

    def create(self, payload):
        return self.connection._call(
            self.CREATE,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
            timeout=(5, 300),
        )

    def update(self, payload, quota_uuid):
        return self.connection._call(
            self.UPDATE.format(quota_uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
            timeout=(5, 300),
        )
