import os
import sys
import inspect
from ruamel import yaml

from .entity import Entity, EntityTypeBase
from .validator import PropertyValidator
from .deployment import DeploymentType


# PODDeployment

# Note parent class of PODDeploymentType is DeploymentType
# As deployments in profile class need to be of same type

class PODDeploymentType(DeploymentType):
    __schema_name__ = "PODDeployment"
    __openapi_type__ = "app_pod_deployment"

    def get_ref(cls):
        types = EntityTypeBase.get_entity_types()
        ref = types.get("Ref")
        if not ref:
            return
        name = getattr(ref, "__schema_name__")
        bases = (Entity,)
        if ref:
            attrs = {}
            attrs["name"] = str(cls)

            # Note: app_blueprint_deployment kind to be used for pod deployment
            attrs["kind"] = "app_blueprint_deployment"

        return ref(name, bases, attrs)

    def get_task_target(cls):
        return cls.get_ref()


class PODDeploymentValidator(PropertyValidator, openapi_type="app_pod_deployment"):
    __default__ = None
    __kind__ = PODDeploymentType


def pod_deployment(**kwargs):
    name = kwargs.get("name") or getattr(PODDeploymentType, "__schema_name__")
    bases = (Entity,)
    return PODDeploymentType(name, bases, kwargs)


PODDeployment = pod_deployment()


def read_spec(file_location):
    """ Read Deployment/Service Spec """
    # TODO Replace read_spec by read_deployment_spec and read_service_spec

    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(1))), file_location
    )

    with open(file_path, "r") as f:
        spec = yaml.safe_load(f.read())

    # Validation logic lies here for the "deployment" or "service"
    return spec
