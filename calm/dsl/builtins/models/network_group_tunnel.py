from distutils.version import LooseVersion as LV
import uuid

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version

LOG = get_logging_handle(__name__)


# NetworkGroupTunnel


class NetworkGroupTunnelType(EntityType):
    __schema_name__ = "NetworkGroupTunnel"
    __openapi_type__ = "network_group_tunnel"

    def compile(cls):
        cdict = super().compile()

        platform_vpcs = cdict.pop("platform_vpc_uuid_list", [])
        vpc_uuids = []
        vpc_name = None
        vpc_dicts = []
        for vpc in platform_vpcs:
            vpc_dict = vpc.compile()
            vpc_uuid = vpc_dict.get("uuid", None)
            if vpc_uuid:
                vpc_uuids.append(vpc_dict.get("uuid", None))
            vpc_dicts.append(vpc_dict)
        cdict["platform_vpc_uuid_list"] = vpc_uuids

        if len(vpc_dicts) > 0:
            vpc_name = vpc_dicts[0].get("name")

        account_ref = cdict.get("account_reference", None)
        account_uuid = None
        if account_ref and isinstance(account_ref, EntityType):
            account_dict = account_ref.get_dict()
            account_uuid = account_dict.get("uuid", None)

        tunnel_vm_spec_obj = cdict.pop("tunnel_vm_spec", None)
        tunnel_name = cdict.pop("tunnel_reference", "")
        user_tunnel_vm_name = ""
        if tunnel_vm_spec_obj:
            tunnel_vm_spec_dict = tunnel_vm_spec_obj.compile(
                vpc=vpc_name, account_uuid=account_uuid
            )
            cdict["tunnel_vm_spec"] = tunnel_vm_spec_dict
            user_tunnel_vm_name = tunnel_vm_spec_dict.get("vm_name", None)

        if not user_tunnel_vm_name:
            tunnel_vm_spec_dict["vm_name"] = tunnel_name + "_VM"

        tunnel_reference = {
            "kind": "tunnel",
            "name": tunnel_name,
            "uuid": str(uuid.uuid4()),
        }
        cdict["tunnel_reference"] = tunnel_reference
        return cdict


class NetworkGroupTunnelValidator(
    PropertyValidator, openapi_type="network_group_tunnel"
):
    __default__ = None
    __kind__ = NetworkGroupTunnelType


def network_group_tunnel(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return NetworkGroupTunnelType(name, bases, kwargs)


NetworkGroupTunnel = network_group_tunnel()
