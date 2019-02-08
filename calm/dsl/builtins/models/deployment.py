from .entity import EntityType, Entity
from .validator import PropertyValidator


# Deployment


class DeploymentType(EntityType):
    __schema_name__ = "Deployment"


class Deployment(Entity, metaclass=DeploymentType):
    pass


class DeploymentValidator(PropertyValidator, openapi_type="deployment"):

    __default__ = None
    __kind__ = DeploymentType
