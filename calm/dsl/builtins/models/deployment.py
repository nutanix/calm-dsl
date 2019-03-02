from .entity import EntityType, Entity
from .validator import PropertyValidator


# Deployment

class DeploymentType(EntityType):
    __schema_name__ = "Deployment"
    __openapi_type__ = "app_deployment"


class DeploymentValidator(PropertyValidator, openapi_type="app_deployment"):
    __default__ = None
    __kind__ = DeploymentType


def deployment(**kwargs):
    name = getattr(DeploymentType, "__schema_name__")
    bases = (Entity, )
    return DeploymentType(name, bases, kwargs)


Deployment = deployment()
