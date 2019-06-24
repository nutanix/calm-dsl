from .entity import EntityType, Entity
from .validator import PropertyValidator


from .service import service
from .package import package
from .substrate import substrate


# SimpleDeployment


class SimpleDeploymentType(EntityType):
    __schema_name__ = "SimpleDeployment"
    __openapi_type__ = "app_blueprint_simple_deployment"

    def get_task_target(cls):
        return cls.get_ref()


class SimpleDeploymentValidator(
    PropertyValidator, openapi_type="app_blueprint_simple_deployment"
):
    __default__ = None
    __kind__ = SimpleDeploymentType


def simple_deployment(**kwargs):
    name = getattr(SimpleDeploymentType, "__schema_name__")
    bases = (Entity,)
    return SimpleDeploymentType(name, bases, kwargs)


SimpleDeployment = simple_deployment()
