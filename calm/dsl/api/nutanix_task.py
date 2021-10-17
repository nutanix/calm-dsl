from .resource import ResourceAPI


class TaskAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="tasks")
