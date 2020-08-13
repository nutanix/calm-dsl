from .resource import ResourceAPI


class TaskLibraryApi(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="app_tasks")
