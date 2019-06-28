from .entity import EntityType, Entity
from .validator import PropertyValidator


# Service


class ServiceType(EntityType):
    __schema_name__ = "Service"
    __openapi_type__ = "app_service"

    def get_task_target(cls):
        return cls.get_ref()


class ServiceValidator(PropertyValidator, openapi_type="app_service"):
    __default__ = None
    __kind__ = ServiceType


def service(**kwargs):
    name = kwargs.get("name") or getattr(ServiceType, "__schema_name__")
    bases = (Entity,)
    return ServiceType(name, bases, kwargs)


Service = service()
