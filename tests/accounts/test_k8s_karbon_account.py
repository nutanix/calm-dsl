from calm.dsl.builtins import Account, KubernetesAccountSpec, KubernetesAuth
from calm.dsl.constants import PROVIDER


class K8sSpec(KubernetesAccountSpec):

    type = "karbon"
    cluster = "karbon_cluster"


class K8sKarbonAccount(Account):

    provider_type = PROVIDER.ACCOUNT.KUBERNETES
    spec = K8sSpec
