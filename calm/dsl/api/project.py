from .resource import ResourceAPI
from .connection import REQUEST


class ProjectAPI(ResourceAPI):

    def __init__(self, connection):
        super().__init__(connection, resource_type="projects")
        self.CREATE_PREFIX = ResourceAPI.ROOT + "/projects_internal"
        self.INTERNAL_ITEM = self.CREATE_PREFIX + "/{}"

    def create(self, payload):
        return self.connection._call(
            self.CREATE_PREFIX,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def update(self, uuid, payload):
        return self.connection._call(
            self.INTERNAL_ITEM.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    def read(self, id):
        return self.connection._call(
            self.INTERNAL_ITEM.format(id), verify=False, method=REQUEST.METHOD.GET
        )
