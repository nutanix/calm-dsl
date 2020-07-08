from .entity import EntityType, Entity
from .validator import PropertyValidator


# Deployment


class DeploymentType(EntityType):
    __schema_name__ = "Deployment"
    __openapi_type__ = "app_blueprint_deployment"

    def get_task_target(cls):
        return cls.get_ref()

    @classmethod
    def pre_decompile(mcls, cdict, context=[]):

        cdict = super().pre_decompile(cdict, context=context)
        # For now editables are not supported in deployments
        cdict.pop("editables", None)
        return cdict


class DeploymentValidator(PropertyValidator, openapi_type="app_blueprint_deployment"):
    __default__ = None
    __kind__ = DeploymentType


def deployment(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return DeploymentType(name, bases, kwargs)


Deployment = deployment()
