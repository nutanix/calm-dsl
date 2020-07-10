from .entity import Entity
from .validator import PropertyValidator
from .pod_deployment import PODDeploymentType


class SimplePODDeploymentType(PODDeploymentType):
    __schema_name__ = "SimplePODDeployment"
    __openapi_type__ = "app_simple_pod_deployment"

    def extract_deployment(cls):
        return super().extract_deployment(is_simple_deployment=True)


class SimplePODDeploymentValidator(
    PropertyValidator, openapi_type="app_simple_pod_deployment"
):
    __default__ = None
    __kind__ = SimplePODDeploymentType


def simple_pod_deployment(**kwargs):
    name = kwargs.pop("name", None) or getattr(PODDeploymentType, "__schema_name__")
    bases = (Entity,)
    return SimplePODDeploymentType(name, bases, kwargs)


SimplePODDeployment = simple_pod_deployment()
