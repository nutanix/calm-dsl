from .resource import ResourceAPI
from .connection import REQUEST


class EnvironmentAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="environments")

    def list(self, params={}, ignore_error=False):
        return self.connection._call(
            self.LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
            timeout=(5, 300),
        )
