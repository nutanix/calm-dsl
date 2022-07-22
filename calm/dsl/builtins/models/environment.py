import sys

from .entity import EntityType
from .validator import PropertyValidator
from .helper import common as common_helper
from .calm_ref import Ref
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
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

        # environment_infra_list
        environment_infra_list = []

        infra = cdict.get("infra_inclusion_list", [])
        for provider_obj in infra:
            provider_data = provider_obj.get_dict()

            # Check if given account is filtered in project
            infra_account = provider_data["account_reference"]
            infra_account_name = infra_account["name"]
            infra_account_uuid = infra_account["uuid"]
            infra_type = provider_obj.type
            if infra_account["uuid"] not in project_cache_data["accounts_data"].get(
                infra_type, []
            ):
                LOG.error(
                    "Environment uses {} account '{}' which is not added to project {}.".format(
                        infra_type, infra_account_name, project_name
                    )
                )
                sys.exit(-1)

            if infra_type != "nutanix_pc":
                provider_data.pop("subnet_reference_list", None)
                provider_data.pop("external_network_list", None)
                provider_data.pop("default_subnet_reference", None)

            else:
                provider_data["subnet_references"] = provider_data.get(
                    "subnet_reference_list", []
                ) + provider_data.get("external_network_list", [])
                provider_data.pop("subnet_reference_list", None)
                provider_data.pop("external_network_list", None)
                provider_data["cluster_references"] = provider_data.get(
                    "cluster_reference_list", []
                )
                provider_data.pop("cluster_reference_list", None)
                provider_data["vpc_references"] = provider_data.get(
                    "vpc_reference_list", []
                )
                provider_data.pop("vpc_reference_list", None)

                for cluster in provider_data["cluster_references"]:
                    if cluster["uuid"] not in project_cache_data[
                        "whitelisted_clusters"
                    ].get(infra_account_uuid, []):
                        LOG.error(
                            "Environment uses cluster {} for nutanix_pc account {} which is not added to "
                            "project {}.".format(
                                cluster["name"], infra_account_name, project_name
                            )
                        )
                        sys.exit(-1)

                for vpc in provider_data["vpc_references"]:
                    if vpc["uuid"] not in project_cache_data["whitelisted_vpcs"].get(
                        infra_account_uuid, []
                    ):
                        LOG.error(
                            "Environment uses vpc {} for nutanix_pc account {} which is not added to "
                            "project {}.".format(
                                vpc["name"], infra_account_name, project_name
                            )
                        )
                        sys.exit(-1)

                for sub in provider_data["subnet_references"]:
                    if sub["uuid"] not in project_cache_data["whitelisted_subnets"].get(
                        infra_account_uuid, []
                    ):
                        LOG.error(
                            "Environment uses subnet {} for nutanix_pc account {} which is not added to "
                            "project {}.".format(
                                sub["name"], infra_account_name, project_name
                            )
                        )
                        sys.exit(-1)

            environment_infra_list.append(provider_data)

        # environment infra added in 3.2.0
        if environment_infra_list:
            cdict["infra_inclusion_list"] = environment_infra_list

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

            account_cache_data = Cache.get_entity_data_using_uuid(
                entity_type=CACHE.ENTITY.ACCOUNT, uuid=account_uuid
            )
            account_name = account_cache_data.get("name")
            provider_type = account_cache_data.get("provider_type")

            infra_type_account_map[inv_dict[provider_type]] = Ref.Account(account_name)

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
