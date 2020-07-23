from .resource import ResourceAPI
from .connection import REQUEST


class UserAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="users")
