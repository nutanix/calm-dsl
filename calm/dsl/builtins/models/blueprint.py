from .entity import EntityType, Entity
from .validator import PropertyValidator
from .published_service import published_service
from .service import service
from .package import package
from .substrate import substrate
from .ref import ref
from .deployment import deployment

import uuid


# Blueprint


class BlueprintType(EntityType):
    __schema_name__ = "Blueprint"
    __openapi_type__ = "app_blueprint"

    def compile(cls):

        def pod_deployment_creation(cdict):
            """ Implement pod deployment if exists """

            for profile in cdict["app_profile_list"]:
                pod_deployments = getattr(profile, "pod_deployments", [])
                if pod_deployments:
                    delattr(profile, "pod_deployments")

                pod_dict = extract_pod_deployment(pod_deployments)
                profile.deployments.extend(pod_dict["deployment_definition_list"])

                cdict["service_definition_list"].extend(pod_dict["service_definition_list"])
                cdict["package_definition_list"].extend(pod_dict["package_definition_list"])
                cdict["substrate_definition_list"].extend(pod_dict["substrate_definition_list"])
                cdict["published_service_definition_list"].extend(pod_dict["published_service_definition_list"])

            return cdict

        cdict = super().compile()
        cdict = pod_deployment_creation(cdict)
        return cdict


class BlueprintValidator(PropertyValidator, openapi_type="app_blueprint"):
    __default__ = None
    __kind__ = BlueprintType


def blueprint(**kwargs):
    name = getattr(BlueprintType, "__schema_name__")
    bases = (Entity,)
    return BlueprintType(name, bases, kwargs)


Blueprint = blueprint()


def extract_pod_deployment(deployments):
    """ Unzip the pod-deployment to services, packages, substrates """

    service_definition_list = []
    package_definition_list = []
    substrate_definition_list = []
    published_service_definition_list = []
    deployment_definition_list = []

    for dep in deployments:
        pub_service_name = dep.__name__ + "Published_Service"
        ps_options = {"type": "PROVISION_K8S_SERVICE"}
        ps_options = {**ps_options, **dep.service_spec}

        ps = published_service(name=pub_service_name, options=ps_options)
        published_service_definition_list.append(ps)

        containers_list = dep.deployment_spec["spec"]["template"]["spec"].pop("containers", None)

        package_references = []
        for container in containers_list:
            img = container.pop("image", "")
            img_pull_policy = container.pop("imagePullPolicy", None)

            container_name = container["name"]

            s = service(
                name=container_name + str(uuid.uuid4())[-10:] + "Service",
                container_spec=container
            )

            if img_pull_policy:
                image_spec = {
                    "image": img,
                    "imagePullPolicy": img_pull_policy
                }

            else:
                image_spec = {"image": img}

            p = package(
                name=container_name + str(uuid.uuid4())[-10:] + "Package",
                image_spec=image_spec,
                type="K8S_IMAGE"
            )
            p.services = [ref(s)]
            package_references.append(ref(p))

            # Storing services and packages to serivce list
            service_definition_list.append(s)
            package_definition_list.append(p)

        sub_provider_spec = dep.deployment_spec["spec"].pop("template", {})
        sub_provider_spec = {**({"type": "PROVISION_K8S_POD"}), **sub_provider_spec}
        sub = substrate(
            name=container_name + str(uuid.uuid4())[-10:] + "Substrate",
            provider_type="K8S_POD",
            provider_spec=sub_provider_spec
        )

        substrate_definition_list.append(sub)

        dep_options = {"type": "PROVISION_K8S_DEPLOYMENT"}
        dep_options = {**dep_options, **(dep.deployment_spec)}
        d = deployment(
            name=dep.__name__,      # Dependecies depends on this name
            options=dep_options,
            type="K8S_DEPLOYMENT",
            max_replicas="100"
        )

        d.published_services = [ref(ps)]
        d.packages = package_references
        d.substrate = ref(sub)
        d.dependencies = getattr(dep, "dependencies")

        deployment_definition_list.append(d)

    return {
        "service_definition_list": service_definition_list,
        "package_definition_list": package_definition_list,
        "substrate_definition_list": substrate_definition_list,
        "published_service_definition_list": published_service_definition_list,
        "deployment_definition_list": deployment_definition_list
    }
