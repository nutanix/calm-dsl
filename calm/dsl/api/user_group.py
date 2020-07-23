from .resource import ResourceAPI


class UserGroupAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="user_groups")
