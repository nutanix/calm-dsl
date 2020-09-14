from .entity import EntityType, Entity
from .validator import PropertyValidator


# SingleVmDeployment


class SingleVmDeploymentType(EntityType):
    __schema_name__ = "SingleVmDeployment"
    __openapi_type__ = "app_blueprint_single_vm_deployment"

    def get_ref(cls):
        """Note: Only deployment-level dependencies in single vm blueprint"""
        return super().get_ref(kind="app_blueprint_deployment")

    def get_task_target(cls):
        cls_ref = cls.get_ref()

        # Note: Service to be appeneded in name for task targets
        cls_ref.kind = "app_service"
        cls_ref.name = str(cls) + "Service"

        return cls_ref


class SingleVmDeploymentValidator(
    PropertyValidator, openapi_type="app_blueprint_single_vm_deployment"
):
    __default__ = None
    __kind__ = SingleVmDeploymentType


def single_vm_deployment(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return SingleVmDeploymentType(name, bases, kwargs)


SingleVmDeployment = single_vm_deployment()
