import sys
from distutils.version import LooseVersion as LV

from .entity import EntityType
from calm.dsl.constants import PROVIDER
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version

LOG = get_logging_handle(__name__)


# Project


class ProjectType(EntityType):
    __schema_name__ = "Project"
    __openapi_type__ = "project"

    def compile(cls):
        cdict = super().compile()

        cdict["account_reference_list"] = []
        cdict["subnet_reference_list"] = []
        cdict["external_network_list"] = []
        cdict["default_subnet_reference"] = {}

        CALM_VERSION = Version.get_version("Calm")
        default_subnet_reference = None

        # Populate accounts
        provider_list = cdict.pop("provider_list", [])
        for provider_obj in provider_list:
            provider_data = provider_obj.get_dict()

            if provider_obj.type == "nutanix_pc":
                if "subnet_reference_list" in provider_data:
                    cdict["subnet_reference_list"].extend(
                        provider_data["subnet_reference_list"]
                    )

                if "external_network_list" in provider_data:
                    for _network in provider_data["external_network_list"]:
                        _network.pop("kind", None)
                        cdict["external_network_list"].append(_network)

                if "default_subnet_reference" in provider_data:
                    # From 3.2, only subnets from local account can be marked as default
                    if provider_data.get("subnet_reference_list") or LV(
                        CALM_VERSION
                    ) < LV("3.2.0"):
                        cdict["default_subnet_reference"] = provider_data[
                            "default_subnet_reference"
                        ]

            if "account_reference" in provider_data:
                cdict["account_reference_list"].append(
                    provider_data["account_reference"]
                )

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
        if not default_env:
            cdict.pop("default_environment_reference", None)

        if not cdict.get("default_subnet_reference"):
            cdict.pop("default_subnet_reference", None)
        return cdict


def project(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return ProjectType(name, bases, kwargs)


Project = project()
