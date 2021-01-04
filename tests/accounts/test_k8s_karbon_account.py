from calm.dsl.builtins import Account, KubernetesAccountSpec
from calm.dsl.constants import PROVIDER, KUBERNETES


class K8sSpec(KubernetesAccountSpec):

    account_type = KUBERNETES.ACCOUNT.KARBON
    cluster = "karbon_cluster"


class K8sKarbonAccount(Account):

    provider_type = PROVIDER.ACCOUNT.KUBERNETES
    spec = K8sSpec
