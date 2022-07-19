from distutils.version import LooseVersion as LV

from calm.dsl.providers.base import get_provider

from .entity import EntityType
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


def project(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return ProjectType(name, bases, kwargs)


Project = project()
