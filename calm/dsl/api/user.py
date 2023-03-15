from .resource import ResourceAPI
from .connection import REQUEST


class UserAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="users")

    # Temporary hack to fix blocker CALM-32740
    def list(self, params={}, ignore_error=False):
        params.pop("sort_attribute", None)
        params.pop("sort_order", None)
        return self.connection._call(
            self.LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
            timeout=(5, 60),
        )
