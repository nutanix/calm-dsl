from .resource import ResourceAPI
from .connection import REQUEST


class ProjectAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="projects")
        self.CREATE_PREFIX = ResourceAPI.ROOT + "/projects_internal"
        self.INTERNAL_ITEM = self.CREATE_PREFIX + "/{}"
        self.CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/calm_projects"
        self.CALM_PROJECTS_PREFIX_ITEM = self.CALM_PROJECTS_PREFIX + "/{}"
        self.TASK_POLL = self.CALM_PROJECTS_PREFIX_ITEM + "/pending_tasks/{}"
        self.USAGE = self.CALM_PROJECTS_PREFIX_ITEM + "/usage"

    def create(self, payload):
        return self.connection._call(
            self.CREATE_PREFIX,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def update(self, uuid, payload):
        return self.connection._call(
            self.CALM_PROJECTS_PREFIX_ITEM.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    def read(self, id):
        return self.connection._call(
            self.INTERNAL_ITEM.format(id), verify=False, method=REQUEST.METHOD.GET
        )

    def usage(self, uuid):
        return self.connection._call(
            self.USAGE.format(id), verify=False, method=REQUEST.METHOD.POST
        )

    def delete(self, uuid):
        return self.connection._call(
            self.CALM_PROJECTS_PREFIX_ITEM.format(uuid),
            verify=False,
            method=REQUEST.METHOD.DELETE,
        )

    def poll_task(self, project_uuid, task_uuid):
        return self.connection._call(
            self.TASK_POLL.format(project_uuid, task_uuid),
            verify=False,
            method=REQUEST.METHOD.GET,
        )
