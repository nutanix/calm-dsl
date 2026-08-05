from .resource import ResourceAPI
from .connection import REQUEST


class TaskLibraryApi(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="app_tasks")

    def share(self, uuid, payload):
        url = self.item_path.format(uuid) + "/share"
        return self.connection._call(
            url,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )
