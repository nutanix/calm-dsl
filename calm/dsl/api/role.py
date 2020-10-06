from .resource import ResourceAPI


class RoleAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="roles")
