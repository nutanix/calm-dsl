import sys

from .ahv_vm_vpc import AhvVpc
from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.store import Cache
from .helper import common as common_helper
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# AHV Nic


class AhvNicType(EntityType):
    __schema_name__ = "AhvNic"
    __openapi_type__ = "vm_ahv_nic"

    def compile(cls):

        cdict = super().compile()

        cls_substrate = common_helper._walk_to_parent_with_given_type(
            cls, "SubstrateType"
        )
        account_uuid = (
            cls_substrate.get_referenced_account_uuid() if cls_substrate else ""
        )

        # Fetch nutanix account in project
        project, project_whitelist = common_helper.get_project_with_pc_account()
        if not account_uuid:
            account_uuid = list(project_whitelist.keys())[0]

        project_whitelist_subnet_uuids = project_whitelist.get(account_uuid, {}).get(
            "subnet_uuids", []
        )

        subnet_ref = cdict.get("subnet_reference") or dict()
        subnet_name = subnet_ref.get("name", "") or ""

        vpc_ref = cdict.get("vpc_reference") or dict()
        vpc_name = vpc_ref.get("name", "") or ""

        if subnet_name.startswith("@@{") and subnet_name.endswith("}@@"):
            cdict["subnet_reference"] = {
                "kind": "subnet",
                "uuid": subnet_name,
            }

        elif subnet_name:
            cluster_name = subnet_ref.get("cluster", "")

            subnet_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.AHV_SUBNET,
                name=subnet_name,
                cluster=cluster_name,
                vpc=vpc_name,
                account_uuid=account_uuid,
            )

            if not subnet_cache_data:
                LOG.debug(
                    "Ahv Subnet (name = '{}') not found in registered Nutanix PC account (uuid = '{}') ".format(
                        subnet_name, account_uuid
                    )
                )
                sys.exit("AHV Subnet {} not found.".format(subnet_name))

            vpc_name = subnet_cache_data.get("vpc_name", "")
            vpc_uuid = subnet_cache_data.get("vpc_uuid", "")
            cluster_name = subnet_cache_data.get("cluster_name", "")

            if (
                cluster_name
                and cls_substrate
                and cls_substrate.provider_spec
                and cls_substrate.provider_spec.cluster
                and cluster_name != str(cls_substrate.provider_spec.cluster)
            ):
                substrate_cluster = str(cls_substrate.provider_spec.cluster)
                if not (
                    substrate_cluster.startswith("@@{")
                    and substrate_cluster.endswith("}@@")
                ):
                    sys.exit(
                        "Cluster mismatch - All VLANs should belong to same cluster"
                    )

            if (
                vpc_name
                and cls_substrate
                and cls_substrate.provider_spec
                and not cls_substrate.provider_spec.cluster
            ):
                sys.exit("Cluster reference is mandatory for Overlay NICs")

            # If substrate defined under environment model
            subnet_uuid = subnet_cache_data.get("uuid", "")
            cls_env = common_helper._walk_to_parent_with_given_type(
                cls, "EnvironmentType"
            )
            if cls_env:
                infra = getattr(cls_env, "providers", [])
                for _pdr in infra:
                    if _pdr.type == "nutanix_pc":
                        subnet_references = getattr(_pdr, "subnet_reference_list", [])
                        subnet_references.extend(
                            getattr(_pdr, "external_network_list", [])
                        )
                        sr_list = [_sr.get_dict()["uuid"] for _sr in subnet_references]
                        if subnet_uuid not in sr_list:
                            LOG.error(
                                "Subnet '{}' not whitelisted in environment '{}'".format(
                                    subnet_name, str(cls_env)
                                )
                            )
                            sys.exit(-1)

            # If provider_spec is defined under substrate and substrate is defined under blueprint model
            elif cls_substrate:
                pfl_env = cls_substrate.get_profile_environment()
                if pfl_env:
                    environment_cache_data = Cache.get_entity_data_using_uuid(
                        entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=pfl_env["uuid"]
                    )
                    if not environment_cache_data:
                        LOG.error(
                            "Environment {} not found. Please run: calm update cache".format(
                                pfl_env["name"]
                            )
                        )
                        sys.exit(-1)

                    env_accounts = environment_cache_data.get("accounts_data", {}).get(
                        "nutanix_pc", []
                    )
                    if subnet_uuid not in env_accounts.get(account_uuid, []):
                        LOG.error(
                            "Subnet {} is not whitelisted in environment {}".format(
                                subnet_name, str(pfl_env)
                            )
                        )
                        sys.exit(-1)

                elif subnet_uuid not in project_whitelist_subnet_uuids:
                    LOG.error(
                        "Subnet {} is not whitelisted in project {}".format(
                            subnet_name, project["name"]
                        )
                    )
                    sys.exit(-1)

            cdict["subnet_reference"] = {
                "kind": "subnet",
                "name": subnet_name,
                "uuid": subnet_uuid,
            }
            if vpc_name:
                cdict["vpc_reference"] = AhvVpc(vpc_name)

        nfc_ref = cdict.get("network_function_chain_reference") or dict()
        nfc_name = nfc_ref.get("name", "")
        if nfc_name:
            nfc_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.AHV_NETWORK_FUNCTION_CHAIN, name=nfc_name
            )

            if not nfc_cache_data:
                LOG.debug(
                    "Ahv Network Function Chain (name = '{}') not found in registered nutanix_pc account (uuid = '{}') in project (name = '{}')".format(
                        nfc_name, account_uuid, project["name"]
                    )
                )
                LOG.error(
                    "AHV Network Function Chain {} not found. Please run: calm update cache".format(
                        nfc_name
                    )
                )
                sys.exit(-1)

            nfc_uuid = nfc_cache_data.get("uuid", "")
            cdict["network_function_chain_reference"] = {
                "name": nfc_name,
                "uuid": nfc_uuid,
                "kind": "network_function_chain",
            }

        return cdict


class AhvNicValidator(PropertyValidator, openapi_type="vm_ahv_nic"):
    __default__ = None
    __kind__ = AhvNicType


def ahv_vm_nic(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvNicType(name, bases, kwargs)


def create_ahv_nic(
    subnet=None,
    network_function_nic_type="INGRESS",
    nic_type="NORMAL_NIC",
    network_function_chain=None,  # TODO Deal with it
    mac_address="",
    ip_endpoints=[],
    cluster=None,
    vpc=None,
):

    if vpc and cluster:
        LOG.error(
            "Invalid params [vpc, subnet] passed for Ahv Subnet (name = '{}'). Ahv Subnet can  have only one of [vpc, cluster]"
        )
        sys.exit("Invalid params [vpc, cluster] passed for subnet {}".format(subnet))
    kwargs = {}

    if subnet:
        # Cluster name is used to find subnet uuid at compile time
        kwargs["subnet_reference"] = {
            "name": subnet,
            "kind": "subnet",
            "cluster": cluster,
        }
    if vpc:
        kwargs["vpc_reference"] = {
            "name": vpc,
            "kind": "vpc",
        }

    if network_function_chain:
        kwargs["network_function_chain_reference"] = {
            "name": network_function_chain,
            "kind": "network_function_chain",
        }

    for ip in ip_endpoints:
        if not kwargs.get("ip_endpoint_list"):
            kwargs["ip_endpoint_list"] = []

        # Note the IP type is set to be ASSIGNED always
        kwargs["ip_endpoint_list"].append({"ip": ip, "type": "ASSIGNED"})

    kwargs.update(
        {
            "network_function_nic_type": network_function_nic_type,
            "nic_type": nic_type,
            "mac_address": mac_address,
        }
    )

    return ahv_vm_nic(**kwargs)


def normal_ingress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="INGRESS",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        vpc=vpc,
    )


def normal_egress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="EGRESS",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        vpc=vpc,
    )


def normal_tap_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="TAP",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        vpc=vpc,
    )


def direct_ingress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="INGRESS",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        vpc=vpc,
    )


def direct_egress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="EGRESS",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        vpc=vpc,
    )


def direct_tap_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="TAP",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        vpc=vpc,
    )


def network_function_ingress_nic(mac_address="", network_function_chain=None):
    return create_ahv_nic(
        network_function_nic_type="INGRESS",
        nic_type="NETWORK_FUNCTION_NIC",
        mac_address=mac_address,
        network_function_chain=network_function_chain,
    )


def network_function_egress_nic(mac_address="", network_function_chain=None):
    return create_ahv_nic(
        network_function_nic_type="EGRESS",
        nic_type="NETWORK_FUNCTION_NIC",
        mac_address=mac_address,
        network_function_chain=network_function_chain,
    )


def network_function_tap_nic(mac_address="", network_function_chain=None):
    return create_ahv_nic(
        network_function_nic_type="TAP",
        nic_type="NETWORK_FUNCTION_NIC",
        mac_address=mac_address,
        network_function_chain=network_function_chain,
    )


class AhvVmNic:
    def __new__(cls, subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None):
        return normal_ingress_nic(
            subnet=subnet,
            mac_address=mac_address,
            ip_endpoints=ip_endpoints,
            cluster=cluster,
            vpc=vpc,
        )

    class NormalNic:
        def __new__(
            cls, subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None
        ):
            return normal_ingress_nic(
                subnet=subnet,
                mac_address=mac_address,
                ip_endpoints=ip_endpoints,
                cluster=cluster,
                vpc=vpc,
            )

        ingress = normal_ingress_nic
        egress = normal_egress_nic
        tap = normal_tap_nic

    class DirectNic:
        def __new__(
            cls, subnet, mac_address="", ip_endpoints=[], cluster=None, vpc=None
        ):
            return direct_ingress_nic(
                subnet=subnet,
                mac_address=mac_address,
                ip_endpoints=ip_endpoints,
                cluster=cluster,
                vpc=vpc,
            )

        ingress = direct_ingress_nic
        egress = direct_egress_nic
        tap = direct_tap_nic

    class NetworkFunctionNic:
        def __new__(cls, mac_address="", network_function_chain=None):
            return network_function_ingress_nic(
                mac_address=mac_address, network_function_chain=network_function_chain
            )

        ingress = network_function_ingress_nic
        egress = network_function_egress_nic
        tap = network_function_tap_nic
