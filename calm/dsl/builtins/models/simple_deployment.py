from .entity import EntityType, Entity
from .validator import PropertyValidator


# SimpleDeployment


class SimpleDeploymentType(EntityType):
    __schema_name__ = "SimpleDeployment"
    __openapi_type__ = "app_blueprint_simple_deployment"

    def get_ref(cls):
        """Note: Only deployment-level dependencies in simple blueprint"""
        return super().get_ref(kind="app_blueprint_deployment")

    def get_task_target(cls):
        cls_ref = cls.get_ref()

        # Note: Service to be appeneded in name for task targets
        cls_ref.kind = "app_service"
        cls_ref.name = str(cls) + "Service"

        return cls_ref


class SimpleDeploymentValidator(
    PropertyValidator, openapi_type="app_blueprint_simple_deployment"
):
    __default__ = None
    __kind__ = SimpleDeploymentType


def simple_deployment(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return SimpleDeploymentType(name, bases, kwargs)


SimpleDeployment = simple_deployment()
