from .entity import EntityType, Entity
from .validator import PropertyValidator


# Service


class PublishedServiceType(EntityType):
    __schema_name__ = "PublishedService"
    __openapi_type__ = "app_published_service"

    def get_task_target(cls):
        return cls.get_ref()


class PublishedServiceValidator(
    PropertyValidator, openapi_type="app_published_service"
):
    __default__ = None
    __kind__ = PublishedServiceType


def published_service(**kwargs):
    name = "_" + getattr(PublishedServiceType, "__schema_name__")
    name = kwargs.get("name", name)
    bases = (Entity,)
    return PublishedServiceType(name, bases, kwargs)


PublishedService = published_service()
