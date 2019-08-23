from .entity import EntityType, Entity
from .validator import PropertyValidator


# PODDeployment


class PODDeploymentType(EntityType):
    __schema_name__ = "PODDeployment"
    __openapi_type__ = "app_pod_deployment"

    def get_task_target(cls):
        return cls.get_ref()


class PODDeploymentValidator(PropertyValidator, openapi_type="app_pod_deployment"):
    __default__ = None
    __kind__ = PODDeploymentType


def pod_deployment(**kwargs):
    name = kwargs.get("name") or getattr(PODDeploymentType, "__schema_name__")
    bases = (Entity,)
    return PODDeploymentType(name, bases, kwargs)


PODDeployment = pod_deployment()
