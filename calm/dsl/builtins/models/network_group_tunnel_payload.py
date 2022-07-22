from calm.dsl.api import tunnel
from .entity import EntityType, Entity
from .validator import PropertyValidator
from .network_group_tunnel import NetworkGroupTunnelType
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Blueprint Payload


class NetworkGroupTunnelPayloadType(EntityType):
    __schema_name__ = "NetworkGroupTunnelPayload"
    __openapi_type__ = "app_network_group_tunnel_payload"


class NetworkGroupTunnelPayloadValidator(
    PropertyValidator, openapi_type="app_network_group_tunnel_payload"
):
    __default__ = None
    __kind__ = NetworkGroupTunnelPayloadType


def _network_group_tunnel_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return NetworkGroupTunnelPayloadType(name, bases, kwargs)


NetworkGroupTunnelPayload = _network_group_tunnel_payload()


def create_network_group_tunnel_payload(UserNetworkGroupTunnel):

    err = {"error": "", "code": -1}

    if UserNetworkGroupTunnel is None:
        err["error"] = "Given network group tunnel is empty."
        return None, err

    if not isinstance(UserNetworkGroupTunnel, NetworkGroupTunnelType):
        err["error"] = "Given network group tunnel is not of type NetworkGroupTunnel"
        return None, err

    UserNetworkGroupTunnelPayload = _network_group_tunnel_payload()

    tunnel_name = UserNetworkGroupTunnel.__name__
    UserNetworkGroupTunnel.tunnel_name = tunnel_name
    spec = {
        "name": tunnel_name + "_ng",
        "description": UserNetworkGroupTunnel.__doc__ or "",
        "resources": UserNetworkGroupTunnel,
    }

    metadata = {
        "spec_version": 1,
        "kind": "network_group_tunnel",
        "name": tunnel_name + "_ng",
    }

    UserNetworkGroupTunnelPayload.metadata = metadata
    UserNetworkGroupTunnelPayload.spec = spec

    return UserNetworkGroupTunnelPayload, None
