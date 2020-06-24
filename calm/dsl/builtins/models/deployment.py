from .entity import EntityType, Entity
from .validator import PropertyValidator
from .client_attrs import add_ui_dsl_name_map_entry


# Deployment


class DeploymentType(EntityType):
    __schema_name__ = "Deployment"
    __openapi_type__ = "app_blueprint_deployment"

    def get_task_target(cls):
        return cls.get_ref()

    def compile(cls):

        cdict = super().compile()
        if cdict["name"] != cls.__name__:
            add_ui_dsl_name_map_entry(cdict["name"], cls.__name__)

        return cdict


class DeploymentValidator(PropertyValidator, openapi_type="app_blueprint_deployment"):
    __default__ = None
    __kind__ = DeploymentType


def deployment(**kwargs):
    name = kwargs.get("display_name", None) or kwargs.get("name", None)
    bases = (Entity,)
    return DeploymentType(name, bases, kwargs)


Deployment = deployment()
