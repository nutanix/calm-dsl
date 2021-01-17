from calm.dsl.builtins import Account, KarbonAccountSpec
from calm.dsl.constants import PROVIDER


class K8sSpec(KarbonAccountSpec):

    cluster = "karbon_cluster"


class K8sKarbonAccount(Account):

    provider_type = PROVIDER.NUTANIX
    resource_type = "KARBON"
    spec = K8sSpec
