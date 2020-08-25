import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Blueprint


class BlueprintType(EntityType):
    __schema_name__ = "Blueprint"
    __openapi_type__ = "app_blueprint"

    def compile(cls):
        def unzip_pod_deployments(cdict):
            """ Unzip pod deployment if exists """

            for profile in cdict["app_profile_list"]:
                deployments = getattr(profile, "deployments", [])

                normal_deployments = []
                for dep in deployments:
                    if dep.type == "K8S_DEPLOYMENT":
                        pod_dict = dep.extract_deployment()

                        normal_deployments.extend(
                            pod_dict["deployment_definition_list"]
                        )
                        cdict["package_definition_list"].extend(
                            pod_dict["package_definition_list"]
                        )
                        cdict["substrate_definition_list"].extend(
                            pod_dict["substrate_definition_list"]
                        )
                        cdict["published_service_definition_list"].extend(
                            pod_dict["published_service_definition_list"]
                        )

                    else:
                        normal_deployments.append(dep)

                setattr(profile, "deployments", normal_deployments)

            return cdict

        cdict = super().compile()
        cdict = unzip_pod_deployments(cdict)

        # Searching for brownfield deployments
        is_brownfield = False
        for profile in cdict.get("app_profile_list", []):
            for dep in profile.deployments:
                if dep.type == "BROWNFIELD":
                    is_brownfield = True

        if is_brownfield:
            cdict["type"] = "BROWNFIELD"

            # Multiple profiles are not allowed in brownfield blueprint (UI behaviour)
            if len(cdict["app_profile_list"]) > 1:
                LOG.error("Multiple profiles are not allowed in brownfield application")
                sys.exit(-1)

        return cdict


class BlueprintValidator(PropertyValidator, openapi_type="app_blueprint"):
    __default__ = None
    __kind__ = BlueprintType


def blueprint(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return BlueprintType(name, bases, kwargs)


Blueprint = blueprint()
