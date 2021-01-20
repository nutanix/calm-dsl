import sys

from .entity import EntityType
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


# Project


class ProjectType(EntityType):
    __schema_name__ = "Project"
    __openapi_type__ = "project"

    def compile(cls):
        cdict = super().compile()

        cdict["account_reference_list"] = []
        # Populate accounts
        provider_list = cdict.pop("provider_list", [])
        for provider_obj in provider_list:
            provider_obj = provider_obj.get_dict()
            provider_type = provider_obj["type"]
            if provider_type == "nutanix_pc":
                if "subnet_reference_list" in provider_obj:
                    if cdict.get("subnet_reference_list") is None:
                        cdict["subnet_reference_list"] = []
                    cdict["subnet_reference_list"].extend(
                        provider_obj["subnet_reference_list"]
                    )

                if "external_network_list" in provider_obj:
                    if cdict.get("external_network_list") is None:
                        cdict["external_network_list"] = []
                    for _network in provider_obj["external_network_list"]:
                        _network.pop("kind", None)  # Kind is not expected for external network list
                        cdict["external_network_list"].append(
                            _network
                        )

                # TODO check for account_type, default is blocked for remote_pc after 3.2
                if "default_subnet_reference" in provider_obj and not cdict.get(
                    "default_subnet_reference"
                ):
                    cdict["default_subnet_reference"] = provider_obj[
                        "default_subnet_reference"
                    ]

            cdict["account_reference_list"].append(provider_obj["account_reference"])

        quotas = cdict.pop("quotas", None)
        if quotas:
            project_resources = []
            for qk, qv in quotas.items():
                if qk != "VCPUS":
                    qv *= 1073741824

                project_resources.append({"limit": qv, "resource_type": qk})

            cdict["resource_domain"] = {"resources": project_resources}

        # pop out unnecessary attibutes
        cdict.pop("environment_definition_list", None)
        # empty dict is not accepted for default_environment_reference
        default_env = cdict.get("default_environment_reference")
        if default_env is not None and not default_env:
            cdict.pop("default_environment_reference", None)

        return cdict


def project(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return ProjectType(name, bases, kwargs)


Project = project()
