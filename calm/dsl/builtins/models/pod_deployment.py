from .entity import Entity
from .validator import PropertyValidator
from .provider_spec import provider_spec as get_provider_spec
from .deployment import DeploymentType
from .published_service import published_service
from .service import service
from .package import package
from .substrate import substrate
from .ref import ref
from .deployment import deployment
from .action import action
from inspect import signature
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)
# PODDeployment

# Note parent class of PODDeploymentType is DeploymentType
# As deployments in profile class need to be of same type
# For macros of container, Use:
#   "{}_{}_{}".format(dep.name, container_name, "PublishedService"),


class PODDeploymentType(DeploymentType):
    __schema_name__ = "PODDeployment"
    __openapi_type__ = "app_pod_deployment"

    def get_ref(cls, kind=None):
        """Note: app_blueprint_deployment kind to be used for pod deployment"""
        return super().get_ref(kind=DeploymentType.__openapi_type__)

    def extract_deployment(cls, is_simple_deployment=False):
        """ extract service, packages etc. from service and deployment spec"""

        service_definition_list = []
        package_definition_list = []
        substrate_definition_list = []
        published_service_definition_list = []
        deployment_definition_list = []

        pub_service_name = cls.__name__ + "Published_Service"
        if "apiVersion" in cls.service_spec:
            del cls.service_spec["apiVersion"]
        if "kind" in cls.service_spec:
            del cls.service_spec["kind"]
        ps_options = {"type": "PROVISION_K8S_SERVICE"}
        ps_options = {**ps_options, **cls.service_spec}

        ps = published_service(name=pub_service_name, options=ps_options)
        published_service_definition_list.append(ps)

        containers_list = cls.deployment_spec["spec"]["template"]["spec"].pop(
            "containers", None
        )

        if not is_simple_deployment:
            # In simple deployment there will be no explicit contianers
            if len(containers_list) != len(cls.containers):
                LOG.debug(
                    "No. of container services provided in entity {}: {}, while no. of containers provided in deployment spec: {}".format(
                        cls, len(cls.containers), len(containers_list)
                    )
                )
                raise Exception(
                    "No. of container services does not match k8s deployment spec"
                )

        container_action_map = {}

        for key, value in cls.__dict__.items():
            if isinstance(value, action):
                sig = signature(value.user_func)
                sig_paramter = sig.parameters.get("container_name", None)
                if not sig_paramter:
                    raise Exception(
                        "container name not supplied action '{}' in deployment '{}'".format(
                            key, cls.__name__
                        )
                    )

                container_name = sig_paramter.default
                if container_action_map.get(container_name, None):
                    container_action_map[container_name].append((key, value))
                else:
                    container_action_map[container_name] = [(key, value)]

        package_references = []
        for ind, container in enumerate(containers_list):
            img = container.pop("image", "")
            img_pull_policy = container.pop("imagePullPolicy", None)

            container_name = container["name"].replace("-", "")

            if not is_simple_deployment:
                s = cls.containers[ind]
                s.container_spec = container

            else:
                s = service(
                    name="{}_{}_{}".format(cls.__name__, container_name, "Service"),
                    container_spec=container,
                )

                if container_action_map.get(container_name, None):
                    for service_action in container_action_map[container_name]:
                        (name, func) = service_action
                        setattr(s, name, func)
                    container_action_map.pop(container_name, None)

            if img_pull_policy:
                image_spec = {"image": img, "imagePullPolicy": img_pull_policy}

            else:
                image_spec = {"image": img}

            p = package(
                name="{}_{}_{}".format(cls.__name__, container_name, "Package"),
                image_spec=image_spec,
                type="K8S_IMAGE",
            )
            p.services = [ref(s)]
            package_references.append(ref(p))

            # Storing services and packages to serivce list
            service_definition_list.append(s)
            package_definition_list.append(p)

        # If not existing container's name is provided in action, raise an Exception\
        if container_action_map:
            raise Exception(
                "Unknown containers : {} provided in action".format(
                    list(container_action_map.keys())
                )
            )

        sub_provider_spec = cls.deployment_spec["spec"].pop("template", {})
        sub = substrate(
            name="{}_{}_{}".format(cls.__name__, container_name, "Substrate"),
            provider_type="K8S_POD",
            provider_spec=get_provider_spec(sub_provider_spec),
        )

        substrate_definition_list.append(sub)

        dep_options = {"type": "PROVISION_K8S_DEPLOYMENT"}
        if "apiVersion" in cls.deployment_spec:
            del cls.deployment_spec["apiVersion"]
        if "kind" in cls.deployment_spec:
            del cls.deployment_spec["kind"]
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
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PODDeploymentType(name, bases, kwargs)


PODDeployment = pod_deployment()
