from .resource import ResourceAPI


class AhvVmAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="vms")
