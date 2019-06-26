from .entity import EntityType, Entity, EntityTypeBase
from .validator import PropertyValidator


from .service import service
from .package import package
from .substrate import substrate


# SimpleDeployment


class SimpleDeploymentType(EntityType):
    __schema_name__ = "SimpleDeployment"
    __openapi_type__ = "app_blueprint_simple_deployment"

    def get_ref(cls):
        types = EntityTypeBase.get_entity_types()
        ref = types.get("Ref")
        if not ref:
            return
        name = getattr(ref, "__schema_name__")
        bases = (Entity,)
        if ref:
            attrs = {}

            # Note: Service to be appeneded in name
            attrs["name"] = str(cls) + "Service"

            # Note: app_service kind to be used for simple deployment
            attrs["kind"] = "app_service"

        return ref(name, bases, attrs)

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
