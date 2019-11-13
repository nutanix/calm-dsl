from .entity import EntityType, Entity
from .validator import PropertyValidator


# AHV Nic


class AhvNicType(EntityType):
    __schema_name__ = "AhvNic"
    __openapi_type__ = "vm_ahv_nic"


class AhvNicValidator(PropertyValidator, openapi_type="vm_ahv_nic"):
    __default__ = None
    __kind__ = AhvNicType


def ahv_vm_nic(**kwargs):
    name = getattr(AhvNicType, "__schema_name__")
    bases = (Entity,)
    return AhvNicType(name, bases, kwargs)


def create_ahv_nic(
    subnet=None,
    network_function_nic_type="INGRESS",
    nic_type="NORMAL_NIC",
    network_function_chain=None,  # TODO Deal with it
    mac_address="",
    ip_endpoints=[],
):

    kwargs = {}
    if subnet:
        kwargs["subnet_reference"] = {
            "name": subnet,
            "uuid": "subnet_uuid",  # TODO call api
        }

    if network_function_chain:
        kwargs["network_function_chain_reference"] = {
            "name": network_function_chain,
            "uuid": "network_function_chain_uuid",  # TODO call api
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


def normal_ingress_nic(subnet, mac_address="", ip_endpoints=[]):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="INGRESS",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
    )


def normal_egress_nic(subnet, mac_address="", ip_endpoints=[]):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="EGRESS",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
    )


def normal_tap_nic(subnet, mac_address="", ip_endpoints=[]):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="TAP",
        nic_type="NORMAL_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
    )


def direct_ingress_nic(subnet, mac_address="", ip_endpoints=[]):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="INGRESS",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
    )


def direct_egress_nic(subnet, mac_address="", ip_endpoints=[]):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="EGRESS",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
    )


def direct_tap_nic(subnet, mac_address="", ip_endpoints=[]):
    return create_ahv_nic(
        subnet=subnet,
        network_function_nic_type="TAP",
        nic_type="DIRECT_NIC",
        mac_address=mac_address,
        ip_endpoints=ip_endpoints,
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
    def __new__(cls, subnet, mac_address="", ip_endpoints=[]):
        return normal_ingress_nic(
            subnet=subnet, mac_address=mac_address, ip_endpoints=ip_endpoints
        )

    class NormalNic:
        def __new__(cls, subnet, mac_address="", ip_endpoints=[]):
            return normal_ingress_nic(
                subnet=subnet, mac_address=mac_address, ip_endpoints=ip_endpoints
            )

        ingress = normal_ingress_nic
        egress = normal_egress_nic
        tap = normal_tap_nic

    class DirectNic:
        def __new__(cls, subnet, mac_address="", ip_endpoints=[]):
            return direct_ingress_nic(
                subnet=subnet, mac_address=mac_address, ip_endpoints=ip_endpoints
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
