from .resource import ResourceAPI
from .connection import REQUEST


class ProjectAPI(ResourceAPI):

    def __init__(self, connection):
        super().__init__(connection, resource_type="projects")
        self.CREATE_PREFIX = ResourceAPI.ROOT + "/projects_internal"

    def create(self, payload):
        return self.connection._call(
            self.CREATE_PREFIX,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )
