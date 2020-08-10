from .resource import ResourceAPI


class UserAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="users")
