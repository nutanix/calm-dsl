from calm.dsl.builtins import NetworkGroupTunnel
from calm.dsl.builtins import Provider, Ref
from calm.dsl.builtins.models.network_group_tunnel_vm_spec import ahv_network_group_tunnel_vm_spec

class NewNetworkGroupTunnel2(NetworkGroupTunnel):
    """Network group tunnel for test"""
    account = Ref.Account("NTNX_LOCAL_AZ")
    platform_vpcs = [Ref.Vpc("test_ng_vpc_61ee30a66f0b", account_name="NTNX_LOCAL_AZ")] # Resolve account name from parent.
    tunnel_vm_spec = ahv_network_group_tunnel_vm_spec("auto_cluster_prod_4fee9603c584", "ng_tunnel_vpc_subnet_e61ad7fdb778")

