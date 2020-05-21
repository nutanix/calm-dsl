from .resource import ResourceAPI
from .connection import REQUEST


class AhvVmAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="vms")
        self.POLL_TASK = ResourceAPI.ROOT + "/tasks/{}"

    def get_task(self, uuid):
        return self.connection._call(
            self.POLL_TASK.format(uuid), verify=False, method=REQUEST.METHOD.GET
        )
