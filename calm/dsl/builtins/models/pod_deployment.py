from .entity import Entity
from .validator import PropertyValidator
from .deployment import DeploymentType
from .published_service import published_service
from .service import service
from .package import package
from .substrate import substrate
from .ref import ref
from .deployment import deployment

import uuid

# PODDeployment

# Note parent class of PODDeploymentType is DeploymentType
# As deployments in profile class need to be of same type


class PODDeploymentType(DeploymentType):
    __schema_name__ = "PODDeployment"
    __openapi_type__ = "app_pod_deployment"

    def get_ref(cls, kind=None):
        """Note: app_blueprint_deployment kind to be used for pod deployment"""
        return super().get_ref(kind="app_blueprint_deployment")

    def extract_deployment(cls):
        """ extract service, packages etc. from service and deployment spec"""

        service_definition_list = []
        package_definition_list = []
        substrate_definition_list = []
        published_service_definition_list = []
        deployment_definition_list = []

        pub_service_name = cls.__name__ + "Published_Service"
        ps_options = {"type": "PROVISION_K8S_SERVICE"}
        ps_options = {**ps_options, **cls.service_spec}

        ps = published_service(name=pub_service_name, options=ps_options)
        published_service_definition_list.append(ps)

        containers_list = cls.deployment_spec["spec"]["template"]["spec"].pop(
            "containers", None
        )

        package_references = []
        for container in containers_list:
            img = container.pop("image", "")
            img_pull_policy = container.pop("imagePullPolicy", None)

            container_name = container["name"]

            s = service(
                name=container_name + str(uuid.uuid4())[-10:] + "Service",
                container_spec=container,
            )

            if img_pull_policy:
                image_spec = {"image": img, "imagePullPolicy": img_pull_policy}

            else:
                image_spec = {"image": img}

            p = package(
                name=container_name + str(uuid.uuid4())[-10:] + "Package",
                image_spec=image_spec,
                type="K8S_IMAGE",
            )
            p.services = [ref(s)]
            package_references.append(ref(p))

            # Storing services and packages to serivce list
            service_definition_list.append(s)
            package_definition_list.append(p)

        sub_provider_spec = cls.deployment_spec["spec"].pop("template", {})
        sub_provider_spec = {**({"type": "PROVISION_K8S_POD"}), **sub_provider_spec}
        sub = substrate(
            name=container_name + str(uuid.uuid4())[-10:] + "Substrate",
            provider_type="K8S_POD",
            provider_spec=sub_provider_spec,
        )

        substrate_definition_list.append(sub)

        dep_options = {"type": "PROVISION_K8S_DEPLOYMENT"}
        dep_options = {**dep_options, **(cls.deployment_spec)}
        d = deployment(
            name=cls.__name__,  # Dependecies depends on this name
            options=dep_options,
            type="K8S_DEPLOYMENT",
            max_replicas="100",
        )

        d.published_services = [ref(ps)]
        d.packages = package_references
        d.substrate = ref(sub)
        d.dependencies = getattr(cls, "dependencies")

        deployment_definition_list.append(d)

        return {
            "service_definition_list": service_definition_list,
            "package_definition_list": package_definition_list,
            "substrate_definition_list": substrate_definition_list,
            "published_service_definition_list": published_service_definition_list,
            "deployment_definition_list": deployment_definition_list,
        }


class PODDeploymentValidator(PropertyValidator, openapi_type="app_pod_deployment"):
    __default__ = None
    __kind__ = PODDeploymentType


def pod_deployment(**kwargs):
    name = kwargs.get("name") or getattr(PODDeploymentType, "__schema_name__")
    bases = (Entity,)
    return PODDeploymentType(name, bases, kwargs)


PODDeployment = pod_deployment()
