from .resource import ResourceAPI


class PolicyAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="policies")
