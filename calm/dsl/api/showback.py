from .resource import ResourceAPI
from .connection import REQUEST


class ShowbackAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="app_showback")

    def status(self):
        return self.connection._call(
            self.ITEM.format("status"), verify=False, method=REQUEST.METHOD.GET
        )
