from .resource import ResourceAPI


class EnvironmentAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="environments")
