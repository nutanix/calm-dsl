import sys

from .entity import EntityType
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


# Project


class AhvProjectType(EntityType):
    __schema_name__ = "AhvProject"
    __openapi_type__ = "app_ahv_project"

    def compile(cls):
        cdict = super().compile()

        cdict["account_reference_list"] = []

        # Populate accounts
        registered_providers = []
        provider_list = cdict.pop("provider_list", [])
        for provider_obj in provider_list:

            # Only single account per provider is allowed
            provider_type = provider_obj["provider_type"]

            if provider_obj["provider_type"] not in registered_providers:
                registered_providers.append(provider_obj["provider_type"])
            else:
                LOG.error(
                    "Multiple accounts of same provider({}) found".format(
                        provider_obj["provider_type"]
                    )
                )
                sys.exit(-1)

            if provider_type == "nutanix_pc":
                if "subnet_reference_list" in provider_obj:
                    cdict["subnet_reference_list"] = provider_obj[
                        "subnet_reference_list"
                    ]

                elif "external_network_list" in provider_obj:
                    cdict["external_network_list"] = provider_obj[
                        "external_network_list"
                    ]

                if "default_subnet_reference" in provider_obj:
                    cdict["default_subnet_reference"] = provider_obj[
                        "default_subnet_reference"
                    ]

            cdict["account_reference_list"].append(provider_obj["account_reference"])

        # Extracting user groups from user_reference_list
        user_references = []
        user_group_references = []
        for user in cdict.pop("user_reference_list", []):
            if user["kind"] == "user":
                user_references.append(user)

            elif user["kind"] == "user_group":
                user_group_references.append(user)

            else:
                LOG.error("Invalid reference object '{}'".format(user["kind"]))

        if user_references:
            cdict["user_reference_list"] = user_references

        if user_group_references:
            cdict["external_user_group_reference_list"] = user_group_references

        return cdict


def ahv_project(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return AhvProjectType(name, bases, kwargs)


AhvProject = ahv_project()
