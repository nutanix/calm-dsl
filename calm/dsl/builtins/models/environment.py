import sys

from .entity import EntityType
from .validator import PropertyValidator
from .metadata_payload import get_metadata_obj
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache

LOG = get_logging_handle(__name__)


# Project


class EnvironmentType(EntityType):
    __schema_name__ = "Environment"
    __openapi_type__ = "environment"  # TODO use mentioned in calm api schemas

    def compile(cls):
        cdict = super().compile()

        substrates = cdict.get("substrate_definition_list", [])

        # ensure that infra_inclusion_list only contains items whitelisted in the project
        metadata_obj = get_metadata_obj()
        project_ref = metadata_obj.get("project_reference", {})
        context = get_context()
        project_config = context.get_project_config()
        project_name = project_ref.get("name", project_config["name"])
        project_cache_data = Cache.get_entity_data(
            entity_type="project", name=project_name
        )
        if not project_cache_data:
            LOG.error(
                "Project {} not found. Please run: calm update cache".format(
                    project_name
                )
            )
            sys.exit(-1)

        infra = cdict.get("infra_inclusion_list", [])
        for row in infra:
            infra_account_uuid = row["account_reference"].get("uuid", "")
            infra_acc = row["account_reference"].get("name", infra_account_uuid)
            infra_type = row["type"]
            if infra_account_uuid not in project_cache_data["accounts_data"].get(
                infra_type, []
            ):
                LOG.error(
                    "Environment uses {} account {} which is not added to project {}.".format(
                        infra_type, infra_acc, project_name
                    )
                )
                sys.exit(-1)
            if infra_type == "nutanix_pc":
                infra_account_subnets = row.get("subnet_references", [])
                for sub in infra_account_subnets:
                    infra_sub_uuid = sub.get("uuid", "")
                    infra_sub = sub.get("name", infra_sub_uuid)
                    if infra_sub_uuid not in project_cache_data[
                        "whitelisted_subnets"
                    ].get(infra_account_uuid, []):
                        LOG.error(
                            "Environment uses subnet {} for nutanix_pc account {} which is not added to "
                            "project {}.".format(infra_sub, infra_acc, project_name)
                        )
                        sys.exit(-1)

        # NOTE Only one substrate per (provider_type, os_type) tuple can exist
        sub_set = set()
        for sub in substrates:
            _sub_tuple = (sub.provider_type, sub.os_type)
            if _sub_tuple in sub_set:
                LOG.error(
                    "Multiple substrates of provider_type '{}' for os type '{}' in an environment are not allowed.".format(
                        sub.provider_type, sub.os_type
                    )
                )
                sys.exit(-1)

            else:
                sub_set.add(_sub_tuple)

        return cdict


class EnvironmentValidator(PropertyValidator, openapi_type="environment"):
    __default__ = None
    __kind__ = EnvironmentType


def environment(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return EnvironmentType(name, bases, kwargs)


Environment = environment()
