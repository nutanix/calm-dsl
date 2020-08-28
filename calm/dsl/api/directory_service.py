from .resource import ResourceAPI


class DirectoryServiceAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="directory_services")
