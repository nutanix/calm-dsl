from .entity import EntityType, Entity
from .validator import PropertyValidator
from .project import ProjectType


# Blueprint Payload


class ProjectPayloadType(EntityType):
    __schema_name__ = "ProjectPayload"
    __openapi_type__ = "app_project_payload"


class ProjectPayloadValidator(PropertyValidator, openapi_type="app_project_payload"):
    __default__ = None
    __kind__ = ProjectPayloadType


def _project_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ProjectPayloadType(name, bases, kwargs)


ProjectPayload = _project_payload()


def create_project_payload(UserProject):

    err = {"error": "", "code": -1}

    if UserProject is None:
        err["error"] = "Given project is empty."
        return None, err

    if not isinstance(UserProject, ProjectType):
        err["error"] = "Given project is not of type Project"
        return None, err

    spec = {
        "name": UserProject.__name__,
        "description": UserProject.__doc__ or "",
        "resources": UserProject,
    }

    metadata = {"spec_version": 1, "kind": "project", "name": UserProject.__name__}

    UserProjectPayload = _project_payload()
    UserProjectPayload.metadata = metadata
    UserProjectPayload.spec = spec

    return UserProjectPayload, None
