from calm.dsl.api import network_group, tunnel
from calm.dsl.builtins.models.helper.common import get_network_group_by_tunnel_name
from .entity import EntityType, Entity
from .validator import PropertyValidator
from .network_group_tunnel_vm_spec import NetworkGroupTunnelVMSpecType
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Blueprint Payload


class NetworkGroupTunnelVMPayloadType(EntityType):
    __schema_name__ = "NetworkGroupTunnelVMPayload"
    __openapi_type__ = "app_network_group_tunnel_vm_payload"


class NetworkGroupTunnelVMPayloadValidator(
    PropertyValidator, openapi_type="app_network_group_tunnel_vm_payload"
):
    __default__ = None
    __kind__ = NetworkGroupTunnelVMPayloadType


def _network_group_tunnel_vm_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return NetworkGroupTunnelVMPayloadType(name, bases, kwargs)


NetworkGroupTunnelPayload = _network_group_tunnel_vm_payload()


def create_network_group_tunnel_vm_payload(
    UserNetworkGroupTunnelVM, network_group_tunnel_name
):

    err = {"error": "", "code": -1}

    if UserNetworkGroupTunnelVM is None:
        err["error"] = "Given network group tunnel is empty."
        return None, err

    if not isinstance(UserNetworkGroupTunnelVM, NetworkGroupTunnelVMSpecType):
        err["error"] = "Given network group tunnel is not of type NetworkGroupTunnel"
        return None, err

    UserNetworkGroupTunnelVMPayload = _network_group_tunnel_vm_payload()

    spec = {
        "name": network_group_tunnel_name,
        "description": UserNetworkGroupTunnelVM.__doc__ or "",
        "resources": UserNetworkGroupTunnelVM,
    }

    if UserNetworkGroupTunnelVM.vm_name == "":
        UserNetworkGroupTunnelVM.vm_name = network_group_tunnel_name + "_VM"

    metadata = {
        "spec_version": 1,
        "kind": "network_group_tunnel_vm",
        "name": network_group_tunnel_name,
    }

    UserNetworkGroupTunnelVMPayload.metadata = metadata
    UserNetworkGroupTunnelVMPayload.spec = spec

    return UserNetworkGroupTunnelVMPayload, None
