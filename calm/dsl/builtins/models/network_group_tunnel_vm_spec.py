from distutils.version import LooseVersion as LV

from calm.dsl.db.table_config import AhvClustersCache, AhvSubnetsCache
from .validator import PropertyValidator
from .entity import EntityType, Entity
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version

LOG = get_logging_handle(__name__)


# NetworkGroupTunnelVMSpec


class NetworkGroupTunnelVMSpecType(EntityType):
    __schema_name__ = "NetworkGroupTunnelVMSpec"
    __openapi_type__ = "network_group_tunnel_vm_spec"

    def compile(cls, **kwargs):
        cdict = super().compile()

        cluster = cdict.pop("cluster", None)
        account_uuid = None

        vpc = kwargs.get("vpc", None)

        if kwargs.get("account_uuid"):
            LOG.debug("Found account_uuid passed from parent compile")
            account_uuid = account_uuid

        if cluster:
            cluster_dict = AhvClustersCache.get_entity_data(
                cluster, account_uuid=account_uuid
            )
            cdict["cluster_uuid"] = cluster_dict.get("uuid")

        subnet = cdict.pop("subnet", None)
        if subnet:
            subnet_dict = AhvSubnetsCache.get_entity_data(
                subnet, account_uuid=account_uuid, vpc=vpc
            )
            cdict["subnet_uuid"] = subnet_dict.get("uuid")

        return cdict


class NetworkGroupTunnelVMSpecValidator(
    PropertyValidator, openapi_type="network_group_tunnel_vm_spec"
):
    __default__ = {}
    __kind__ = NetworkGroupTunnelVMSpecType


def network_group_tunnel_vm_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = ()
    return NetworkGroupTunnelVMSpecType(name, bases, kwargs)


NetworkGroupTunnelVMSpec = network_group_tunnel_vm_spec()


def ahv_network_group_tunnel_vm_spec(cluster, subnet):
    vm_spec_dict = {}
    vm_spec_dict["cluster"] = cluster
    vm_spec_dict["subnet"] = subnet
    vm_spec_dict["type"] = "AHV"
    return network_group_tunnel_vm_spec(**vm_spec_dict)
