from .entity import EntityType


# Project


class AhvProjectType(EntityType):
    __schema_name__ = "AhvProject"
    __openapi_type__ = "app_ahv_project"


def ahv_project(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return AhvProjectType(name, bases, kwargs)


AhvProject = ahv_project()
