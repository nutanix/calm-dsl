from .entity import EntityType, Entity
from .validator import PropertyValidator


# Deployment


class DeploymentType(EntityType):
    __schema_name__ = "Deployment"
    __openapi_type__ = "app_blueprint_deployment"

    def get_task_target(cls):
        return cls.get_ref()


class DeploymentValidator(PropertyValidator, openapi_type="app_blueprint_deployment"):
    __default__ = None
    __kind__ = DeploymentType


def deployment(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return DeploymentType(name, bases, kwargs)


Deployment = deployment()
