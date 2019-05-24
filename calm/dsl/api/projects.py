from .resource import ResourceAPI
import time


class ProjectAPI(ResourceAPI):

    CREATE_PREFIX = ResourceAPI.PREFIX + "projects_internal"
    _PREFIX = ResourceAPI.PREFIX + "projects"
    _LIST = _PREFIX + "/list"
    _ITEM = _PREFIX + "/{}"

    def create(self, payload):
        res, err = self.connection._call(
            self.CREATE_PREFIX,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

        time.sleep(8)  # Project apis are intentful , wait to get consumed
        return res, err

    def delete(self, uuid):
        res, err = super.delete(self, uuid)

        time.sleep(10)  # Wait for Project delete api to get consumed
        return res, err
