from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.store import Cache


# AHV Nic


class AhvNicType(EntityType):
    __schema_name__ = "AhvNic"
    __openapi_type__ = "vm_ahv_nic"

    def compile(cls):
        cdict = super().compile()
        if "mac_address" in cdict and cdict["mac_address"] == "":
            cdict.pop("mac_address")

        if "uuid" in cdict and cdict["uuid"] == "":
            cdict.pop("uuid")

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
    uuid="",
):

    kwargs = {}
    if subnet:
        subnet_cache_data = Cache.get_entity_data(
            entity_type="ahv_subnet", name=subnet, cluster=cluster
        )

        if not subnet_cache_data:
            raise Exception(
                "AHV Subnet {} not found. Please run: calm update cache".format(subnet)
            )

        subnet_uuid = subnet_cache_data.get("uuid", "")
        kwargs["subnet_reference"] = {"name": subnet, "uuid": subnet_uuid}

    if network_function_chain:
        nfc_cache_data = Cache.get_entity_data(
            entity_type="ahv_network_function_chain", name=network_function_chain
        )

        if not nfc_cache_data:
            raise Exception(
                "AHV Network Function Chain {} not found. Please run: calm update cache".format(
                    network_function_chain
                )
            )

        nfc_uuid = nfc_cache_data.get("uuid", "")
        kwargs["network_function_chain_reference"] = {
            "name": network_function_chain,
            "uuid": nfc_uuid,
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
            "uuid": uuid,
        }
    )

    return ahv_vm_nic(**kwargs)


def normal_ingress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="INGRESS",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        uuid=uuid,
    )


def normal_egress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="EGRESS",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        uuid=uuid,
    )


def normal_tap_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="TAP",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        uuid=uuid,
    )


def direct_ingress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="INGRESS",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        uuid=uuid,
    )


def direct_egress_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="EGRESS",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        uuid=uuid,
    )


def direct_tap_nic(subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="TAP",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
        cluster=cluster,
        uuid=uuid,
    )


def network_function_ingress_nic(mac_address="", network_function_chain=None, uuid=""):
    return create_ahv_nic(
        network_function_nic_type="INGRESS",
        nic_type="NETWORK_FUNCTION_NIC",
        mac_address=mac_address,
        network_function_chain=network_function_chain,
        uuid=uuid,
    )


def network_function_egress_nic(mac_address="", network_function_chain=None, uuid=""):
    return create_ahv_nic(
        network_function_nic_type="EGRESS",
        nic_type="NETWORK_FUNCTION_NIC",
        mac_address=mac_address,
        network_function_chain=network_function_chain,
        uuid=uuid,
    )


def network_function_tap_nic(mac_address="", network_function_chain=None, uuid=""):
    return create_ahv_nic(
        network_function_nic_type="TAP",
        nic_type="NETWORK_FUNCTION_NIC",
        mac_address=mac_address,
        network_function_chain=network_function_chain,
        uuid=uuid,
    )


class AhvVmNic:
    def __new__(cls, subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""):
        return normal_ingress_nic(
            subnet=subnet,
            mac_address=mac_address,
            ip_endpoints=ip_endpoints,
            cluster=cluster,
            uuid=uuid,
        )

    class NormalNic:
        def __new__(
            cls, subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""
        ):
            return normal_ingress_nic(
                subnet=subnet,
                mac_address=mac_address,
                ip_endpoints=ip_endpoints,
                cluster=cluster,
                uuid=uuid,
            )

        ingress = normal_ingress_nic
        egress = normal_egress_nic
        tap = normal_tap_nic

    class DirectNic:
        def __new__(
            cls, subnet, mac_address="", ip_endpoints=[], cluster=None, uuid=""
        ):
            return direct_ingress_nic(
                subnet=subnet,
                mac_address=mac_address,
                ip_endpoints=ip_endpoints,
                cluster=cluster,
                uuid=uuid,
            )

        ingress = direct_ingress_nic
        egress = direct_egress_nic
        tap = direct_tap_nic

    class NetworkFunctionNic:
        def __new__(cls, mac_address="", network_function_chain=None, uuid=""):
            return network_function_ingress_nic(
                mac_address=mac_address,
                network_function_chain=network_function_chain,
                uuid=uuid,
            )

        ingress = network_function_ingress_nic
        egress = network_function_egress_nic
        tap = network_function_tap_nic
