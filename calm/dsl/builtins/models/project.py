from .entity import EntityType


# Project


class ProjectType(EntityType):
    __schema_name__ = "Project"
    __openapi_type__ = "app_project"


def project(**kwargs):
    name = getattr(ProjectType, "__schema_name__")
    bases = ()
    return ProjectType(name, bases, kwargs)


Project = project()
