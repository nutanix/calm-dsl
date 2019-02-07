from .entity import EntityType, Entity
from .validator import PropertyValidator
from .base import SCHEMAS


## Deployment


class DeploymentType(EntityType):
    __schema__ = SCHEMAS["Deployment"]


class Deployment(Entity, metaclass=DeploymentType):
    pass


class DeploymentValidator(PropertyValidator, openapi_type="deployment"):

    __default__ = None
    __kind__ = DeploymentType


class DeploymentListValidator(DeploymentValidator, openapi_type="deployments"):

    __default__ = []
