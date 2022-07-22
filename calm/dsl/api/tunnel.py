from .resource import ResourceAPI


class TunnelAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="tunnels")
