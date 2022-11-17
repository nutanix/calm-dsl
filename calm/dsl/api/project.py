from distutils.version import LooseVersion as LV

from .resource import ResourceAPI
from .connection import REQUEST


class ProjectAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="projects")

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

        from calm.dsl.store.version import Version

        calm_version = Version.get_version("Calm")

        if LV(calm_version) > LV("3.5.0"):
            CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/projects"
        else:
            CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/calm_projects"

        CALM_PROJECTS_ITEM = CALM_PROJECTS_PREFIX + "/{}"
        CALM_PROJECTS_USAGE = CALM_PROJECTS_ITEM + "/usage"

        return self.connection._call(
            CALM_PROJECTS_USAGE.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def update(self, uuid, payload):

        from calm.dsl.store.version import Version

        calm_version = Version.get_version("Calm")
        if LV(calm_version) >= LV("3.5.2") and LV(calm_version) < LV("3.6.1"):
            payload = get_projects_internal_payload(payload)
            CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/projects_internal"
        else:
            CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/projects"

        CALM_PROJECTS_ITEM = CALM_PROJECTS_PREFIX + "/{}"
        return self.connection._call(
            CALM_PROJECTS_ITEM.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    def delete(self, uuid):

        from calm.dsl.store.version import Version

        calm_version = Version.get_version("Calm")

        if LV(calm_version) > LV("3.5.0"):
            CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/projects"
        else:
            CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/calm_projects"

        CALM_PROJECTS_ITEM = CALM_PROJECTS_PREFIX + "/{}"

        return self.connection._call(
            CALM_PROJECTS_ITEM.format(uuid),
            verify=False,
            method=REQUEST.METHOD.DELETE,
        )

    def read_pending_task(self, uuid, task_uuid):

        from calm.dsl.store.version import Version

        calm_version = Version.get_version("Calm")

        if LV(calm_version) > LV("3.5.0"):
            CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/projects"
        else:
            CALM_PROJECTS_PREFIX = ResourceAPI.ROOT + "/calm_projects"

        CALM_PROJECTS_ITEM = CALM_PROJECTS_PREFIX + "/{}"
        CALM_PROJECTS_PENDING_TASKS = CALM_PROJECTS_ITEM + "/pending_tasks/{}"

        return self.connection._call(
            CALM_PROJECTS_PENDING_TASKS.format(uuid, task_uuid),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    # https://jira.nutanix.com/browse/CALM-32302
    # Project list timeout if we have more Projects.
    # So setting read timeout to 300 seconds
    def list(self, params={}, ignore_error=False):
        return self.connection._call(
            self.LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
            timeout=(5, 300),
        )


def get_projects_internal_payload(payload):
    """Modify projects paylaod to projects internal payload

    Args:
        payload (dict): project payload

    Returns:
        dict: projects internal payload
    """

    spec = payload["spec"]
    spec["project_detail"] = {"name": spec["name"], "resources": spec["resources"]}
    if "description" in spec:
        spec["project_detail"]["description"] = spec["description"]
        del spec["description"]
    del spec["name"]
    del spec["resources"]
    payload["spec"] = spec

    return payload
