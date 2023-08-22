from .resource import ResourceAPI
from .connection import REQUEST


class ProviderAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="providers", calm_api=True)

        self.CREATE = self.PREFIX

    def create(self, provider_payload):
        return self.connection._call(
            self.CREATE,
            verify=False,
            request_json=provider_payload,
            method=REQUEST.METHOD.POST,
            timeout=(5, 300),
        )
