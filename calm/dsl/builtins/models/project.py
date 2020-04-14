from .entity import EntityType


# Project


class ProjectType(EntityType):
    __schema_name__ = "Project"
    __openapi_type__ = "app_project"


def project(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return ProjectType(name, bases, kwargs)


Project = project()
