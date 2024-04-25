from distutils.version import LooseVersion as LV

from calm.dsl.providers.base import get_provider

from .entity import EntityType

from calm.dsl.api import get_api_client

from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version, Cache

from calm.dsl.builtins.models.providers import Provider
from calm.dsl.builtins.models.calm_ref import Ref

from calm.dsl.constants import CACHE, ACCOUNT

from calm.dsl.providers import get_provider

from calm.dsl.builtins.models.helper.quotas import _get_quota

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
        cdict["cluster_reference_list"] = []
        cdict["vpc_reference_list"] = []

        CALM_VERSION = Version.get_version("Calm")

        # Populate accounts
        provider_list = cdict.pop("provider_list", [])
        for provider_obj in provider_list:
            provider_data = provider_obj.get_dict()

            if provider_obj.type == "nutanix_pc":

                # From 3.5.0 we support Cluster & VPC whitelisting. Client has to take care
                # of sending the respective cluster or vpc if not specified in Project Spec
                if LV(CALM_VERSION) >= LV("3.5.0"):
                    # Get information about all subnets of this account
                    AhvVmProvider = get_provider("AHV_VM")
                    AhvObj = AhvVmProvider.get_api_obj()
                    LOG.debug(
                        "provider_data_subnets:{}".format(
                            provider_data["subnet_reference_list"]
                        )
                    )
                    subnets_list = [
                        subnet["uuid"]
                        for subnet in provider_data["subnet_reference_list"]
                    ]
                    external_subnets_list = [
                        subnet["uuid"]
                        for subnet in provider_data["external_network_list"]
                    ]
                    subnets_list.extend(external_subnets_list)
                    filter_query = ""
                    if subnets_list:
                        filter_query = "_entity_id_=={}".format("|".join(subnets_list))
                    account_uuid = provider_data["account_reference"]["uuid"]
                    subnets = AhvObj.subnets(
                        account_uuid=account_uuid, filter_query=filter_query
                    )
                    subnets = subnets["entities"]
                    LOG.debug("Subnets are: {}".format(subnets))

                    spec_clusters = [
                        cluster["uuid"]
                        for cluster in provider_data["cluster_reference_list"]
                    ]
                    spec_vpcs = [
                        vpc["uuid"] for vpc in provider_data["vpc_reference_list"]
                    ]

                    # Update provider_data with cluster/vpc of the subnets whose vpc/cluster have not been provided in Project Spec.
                    for subnet in subnets:
                        cluster_ref = subnet.get("status", {}).get(
                            "cluster_reference", {}
                        )
                        vpc_ref = (
                            subnet.get("status", {})
                            .get("resources", {})
                            .get("vpc_reference", {})
                        )

                        if cluster_ref and cluster_ref["uuid"] not in spec_clusters:
                            LOG.debug(
                                "Cluster with uuid:{} not present in spec, adding".format(
                                    cluster_ref["uuid"]
                                )
                            )
                            provider_data["cluster_reference_list"].append(
                                {
                                    "kind": "cluster",
                                    "name": cluster_ref.get("name", ""),
                                    "uuid": cluster_ref["uuid"],
                                }
                            )
                            spec_clusters.append(cluster_ref["uuid"])

                        elif vpc_ref and vpc_ref["uuid"] not in spec_vpcs:
                            LOG.debug(
                                "VPC with uuid:{} not present in spec, adding".format(
                                    vpc_ref["uuid"]
                                )
                            )
                            provider_data["vpc_reference_list"].append(
                                {
                                    "kind": "vpc",
                                    "name": vpc_ref.get("name", ""),
                                    "uuid": vpc_ref["uuid"],
                                }
                            )
                            spec_vpcs.append(vpc_ref["uuid"])

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

                if "cluster_reference_list" in provider_data:
                    cdict["cluster_reference_list"].extend(
                        provider_data.get("cluster_reference_list")
                    )

                if "vpc_reference_list" in provider_data:
                    cdict["vpc_reference_list"].extend(
                        provider_data.get("vpc_reference_list")
                    )

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

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        project_uuid = cdict["metadata"]["uuid"]
        cdict = cdict["status"]["resources"]

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        accs = cdict["account_reference_list"]

        subnet_cache_data = [
            Cache.get_entity_data_using_uuid(CACHE.ENTITY.AHV_SUBNET, sub["uuid"])
            for sub in cdict["subnet_reference_list"]
        ]

        cluster_cache_data = [
            Cache.get_entity_data_using_uuid(CACHE.ENTITY.AHV_CLUSTER, cluster["uuid"])
            for cluster in cdict["cluster_reference_list"]
        ]

        vpcs_cache_data = [
            Cache.get_entity_data_using_uuid(CACHE.ENTITY.AHV_VPC, vpc["uuid"])
            for vpc in cdict["vpc_reference_list"]
        ]

        quota_vcpus = 0
        quota_disk = 0
        quota_memory = 0

        _quotas = None

        providers_list = []
        for _acc in accs:
            _provider_data = {}
            account_cache_data = Cache.get_entity_data_using_uuid(
                entity_type=CACHE.ENTITY.ACCOUNT, uuid=_acc["uuid"]
            )

            _provider_data["account_reference"] = {
                "kind": "account",
                "uuid": account_cache_data["uuid"],
            }

            _provider_data["type"] = account_cache_data["provider_type"]

            subnets = []
            cluster_uuids = []
            cluster_names = []
            for subnet in subnet_cache_data:
                if subnet["account_uuid"] == account_cache_data["uuid"]:
                    _subnet = {"kind": "subnet", "uuid": subnet["uuid"]}
                    subnets.append(_subnet)
                    cluster_uuids.append(subnet.get("cluster_uuid", ""))

            _provider_data["subnet_references"] = subnets

            if (
                account_cache_data["provider_type"] == ACCOUNT.TYPE.VMWARE
                or account_cache_data["provider_type"] == ACCOUNT.TYPE.AHV
            ):

                if account_cache_data["provider_type"] == ACCOUNT.TYPE.VMWARE:
                    vmware_provider = get_provider("VMWARE_VM")
                    vmware_provider_obj = vmware_provider.get_api_obj()
                    cluster_names = vmware_provider_obj.clusters(_acc["uuid"])
                    clusters = cluster_names

                if account_cache_data["provider_type"] == ACCOUNT.TYPE.AHV:
                    clusters = cluster_uuids

                for cluster in clusters:
                    quota_entities = {
                        "project": project_uuid,
                        "account": _acc["uuid"],
                        "cluster": cluster,
                    }

                    client = get_api_client()
                    quota = _get_quota(client, quota_entities)

                    if len(quota) != 0 and len(quota[0]["entities"]) != 0:
                        quota_vcpus += quota[0]["entities"][0]["status"]["resources"][
                            "data"
                        ]["vcpu"]
                        quota_disk_ = quota[0]["entities"][0]["status"]["resources"][
                            "data"
                        ]["disk"]
                        quota_disk += int(quota_disk_ / 1073741824)
                        quota_memory_ = quota[0]["entities"][0]["status"]["resources"][
                            "data"
                        ]["memory"]
                        quota_memory += int(quota_memory_ / 1073741824)

            providers_list.append(_provider_data)

        cdict["provider_list"] = providers_list

        if quota_disk != 0 and quota_memory != 0 and quota_vcpus != 0:
            _quotas = {
                "VCPUS": quota_vcpus,
                "STORAGE": quota_disk,
                "MEMORY": quota_memory,
            }
            cdict["quotas"] = _quotas

        return cdict


def project(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return ProjectType(name, bases, kwargs)


Project = project()
