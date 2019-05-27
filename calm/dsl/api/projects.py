from .resource import ResourceAPI
import time


class ProjectAPI(ResourceAPI):

    CREATE_PREFIX = ResourceAPI.PREFIX + "projects_internal"
    PREFIX = ResourceAPI.PREFIX + "projects"
    LIST = PREFIX + "/list"
    ITEM = PREFIX + "/{}"

    def create(self, payload):
        return self.connection._call(
            self.CREATE_PREFIX,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )
