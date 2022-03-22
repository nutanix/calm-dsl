from .resource import ResourceAPI
from .connection import REQUEST


class JobAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="jobs")
        self.INSTANCES = self.ITEM + "/instances"

    def instances(self, uuid, params={}, ignore_error=False):
        return self.connection._call(
            self.INSTANCES.format(uuid),
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
        )
