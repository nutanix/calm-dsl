import sys

from .entity import EntityType
from .validator import PropertyValidator
from .helper import common as common_helper
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.constants import PROVIDER_ACCOUNT_TYPE_MAP

LOG = get_logging_handle(__name__)


# Project


class EnvironmentType(EntityType):
    __schema_name__ = "Environment"
    __openapi_type__ = "environment"  # TODO use mentioned in calm api schemas

    def compile(cls):
        cdict = super().compile()

        substrates = cdict.get("substrate_definition_list", [])

        # ensure that infra_inclusion_list only contains items whitelisted in the project
        project_cache_data = common_helper.get_cur_context_project()
        project_name = project_cache_data.get("name")

        infra = cdict.get("infra_inclusion_list", [])
        for row in infra:
            infra_account_uuid = row["account_reference"].get("uuid", "")
            infra_acc = row["account_reference"].get("name", infra_account_uuid)
            infra_type = row["type"]
            if infra_account_uuid not in project_cache_data["accounts_data"].get(
                infra_type, []
            ):
                LOG.error(
                    "Environment uses {} account '{}' which is not added to project {}.".format(
                        infra_type, infra_acc, project_name
                    )
                )
                sys.exit(-1)

            if infra_type == "nutanix_pc":
                row["subnet_references"] = row.get(
                    "subnet_reference_list", []
                ) + row.get("external_network_list", [])
                for sub in row["subnet_references"]:
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

                row.pop("subnet_reference_list", None)
                row.pop("external_network_list", None)

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

    def post_compile(cls, cdict):
        cdict = super().post_compile(cdict)

        # Substrate should use account defined in the environment only
        inv_dict = {v: k for k, v in PROVIDER_ACCOUNT_TYPE_MAP.items()}
        infra_type_account_map = {}
        infra = cdict.get("infra_inclusion_list", [])
        for row in infra:
            account_ref = row["account_reference"]
            account_uuid = account_ref.get("uuid")

            account_cache_data = Cache.get_entity_data_using_uuid(uuid=account_uuid)
            provider_type = account_cache_data.get("provider_type")

            infra_type_account_map[inv_dict[provider_type]] = account_ref

        if infra_type_account_map:
            substrates = cdict.get("substrate_definition_list", [])
            for sub in substrates:
                provider_type = getattr(sub, "provider_type")
                sub.account = infra_type_account_map[provider_type]

        return cdict


class EnvironmentValidator(PropertyValidator, openapi_type="environment"):
    __default__ = None
    __kind__ = EnvironmentType


def environment(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return EnvironmentType(name, bases, kwargs)


Environment = environment()
