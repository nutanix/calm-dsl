import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .metadata_payload import get_metadata_obj
from calm.dsl.store import Cache
from calm.dsl.config import get_context

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# AHV Nic


class AhvNicType(EntityType):
    __schema_name__ = "AhvNic"
    __openapi_type__ = "vm_ahv_nic"

    def compile(cls):

        cdict = super().compile()

        # Getting the metadata obj
        metadata_obj = get_metadata_obj()
        project_ref = metadata_obj.get("project_reference") or dict()

        # If project not found in metadata, it will take project from config
        context = get_context()
        project_config = context.get_project_config()
        project_name = project_ref.get("name") or project_config["name"]

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

        project_accounts = project_cache_data["accounts_data"]
        project_subnets = project_cache_data["whitelisted_subnets"]
        # Fetch Nutanix_PC account registered
        account_uuid = project_accounts.get("nutanix_pc", "")

        subnet_ref = cdict.get("subnet_reference") or dict()
        if subnet_ref:
            subnet_name = subnet_ref.get("name", "")
            cluster_name = subnet_ref.get("cluster", "")
            subnet_cache_data = Cache.get_entity_data(
                entity_type="ahv_subnet",
                name=subnet_name,
                cluster=cluster_name,
                account_uuid=account_uuid,
            )

            if not subnet_cache_data:
                LOG.debug(
                    "Ahv Subnet (name = '{}') not found in registered nutanix_pc account (uuid = '{}') in project (name = '{}')".format(
                        subnet_name, account_uuid, project_name
                    )
                )
                LOG.error(
                    "AHV Subnet {} not found. Please run: calm update cache".format(
                        subnet_name
                    )
                )
                sys.exit(-1)

            subnet_uuid = subnet_cache_data.get("uuid", "")
            if subnet_uuid not in project_subnets:
                LOG.error(
                    "Subnet {} is not whitelisted in project {}".format(
                        subnet_name, project_name
                    )
                )
                sys.exit(-1)

            cdict["subnet_reference"] = {
                "kind": "subnet",
                "name": subnet_name,
                "uuid": subnet_uuid,
            }

        nfc_ref = cdict.get("network_function_chain_reference") or dict()
        nfc_name = nfc_ref.get("name", "")
        if nfc_name:
            nfc_cache_data = Cache.get_entity_data(
                entity_type="ahv_network_function_chain", name=nfc_name
            )

            if not nfc_cache_data:
                LOG.debug(
                    "Ahv Network Function Chain (name = '{}') not found in registered nutanix_pc account (uuid = '{}') in project (name = '{}')".format(
                        nfc_name, account_uuid, project_name
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
):

    kwargs = {}

    if subnet:
        # Cluster name is used to find subnet uuid at compile time
        kwargs["subnet_reference"] = {
            "name": subnet,
            "kind": "subnet",
            "cluster": cluster,
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


def normal_ingress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="INGRESS",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
    )


def normal_egress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="EGRESS",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
    )


def normal_tap_nic(subnet, mac_address="", ip_endpoints=[], cluster=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="TAP",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
    )


def direct_ingress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="INGRESS",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
    )


def direct_egress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="EGRESS",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
    )


def direct_tap_nic(subnet, mac_address="", ip_endpoints=[], cluster=None):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="TAP",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
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
    def __new__(cls, subnet, mac_address="", ip_endpoints=[], cluster=None):
        return normal_ingress_nic(
            subnet=subnet,
            mac_address=mac_address,
            ip_endpoints=ip_endpoints,
            cluster=cluster,
        )

    class NormalNic:
        def __new__(cls, subnet, mac_address="", ip_endpoints=[], cluster=None):
            return normal_ingress_nic(
                subnet=subnet,
                mac_address=mac_address,
                ip_endpoints=ip_endpoints,
                cluster=cluster,
            )

        ingress = normal_ingress_nic
        egress = normal_egress_nic
        tap = normal_tap_nic

    class DirectNic:
        def __new__(cls, subnet, mac_address="", ip_endpoints=[], cluster=None):
            return direct_ingress_nic(
                subnet=subnet,
                mac_address=mac_address,
                ip_endpoints=ip_endpoints,
                cluster=cluster,
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
