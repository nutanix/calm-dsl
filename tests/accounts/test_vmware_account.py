from calm.dsl.builtins import Account, VmwareAccountSpec
from calm.dsl.constants import PROVIDER


class VmwareSpec(VmwareAccountSpec):

    username = "username"
    datacenter = "datacenter"
    server = "127.0.0.1"
    port = 3201
    password = "vmw_password"


class VmwareAccount(Account):

    provider_type = PROVIDER.ACCOUNT.VMWARE
    spec = VmwareSpec
