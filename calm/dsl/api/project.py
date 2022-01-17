from distutils.version import LooseVersion as LV

from .resource import ResourceAPI
from .connection import REQUEST


class ProjectAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="projects")

        from calm.dsl.store.version import Version
        calm_version = Version.get_version("Calm")

        if LV(calm_version) > LV("3.4.0"):
            self.CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/projects"
        else:
            self.CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/calm_projects"

        self.CALM_PROJECTS_ITEM = self.CALM_PROJECTS_PREFIX + "/{}"
        self.CALM_PROJECTS_PENDING_TASKS = self.CALM_PROJECTS_ITEM + "/pending_tasks/{}"
        self.CALM_PROJECTS_USAGE = self.CALM_PROJECTS_ITEM + "/usage"

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

    def usage(self, uuid, payload):
        return self.connection._call(
            self.CALM_PROJECTS_USAGE.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def delete(self, uuid):
        return self.connection._call(
            self.CALM_PROJECTS_ITEM.format(uuid),
            verify=False,
            method=REQUEST.METHOD.DELETE,
        )

    def read_pending_task(self, uuid, task_uuid):
        return self.connection._call(
            self.CALM_PROJECTS_PENDING_TASKS.format(uuid, task_uuid),
            verify=False,
            method=REQUEST.METHOD.GET,
        )
