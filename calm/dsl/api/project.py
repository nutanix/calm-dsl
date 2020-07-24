from .resource import ResourceAPI
from .connection import REQUEST


class ProjectAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="projects")
        self.CREATE_INTERNAL_PREFIX = ResourceAPI.ROOT + "/projects_internal"
        self.INTERNAL_ITEM = self.CREATE_INTERNAL_PREFIX + "/{}"

    def create_internal(self, payload):
        return self.connection._call(
            self.CREATE_INTERNAL_PREFIX,
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

    def create(self, payload):

        project_name = payload["spec"].get("name") or payload["metadata"].get("name")

        # check if project with the given name already exists
        params = {"filter": "name=={}".format(project_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)

        if entities:
            err_msg = "Project {} already exists.".format(project_name)

            err = {"error": err_msg, "code": -1}
            return None, err

        return super().create(payload)
