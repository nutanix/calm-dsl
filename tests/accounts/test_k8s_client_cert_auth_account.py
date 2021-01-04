from calm.dsl.builtins import Account, KubernetesAccountSpec, KubernetesAuth
from calm.dsl.constants import PROVIDER, KUBERNETES


class K8sSpec(KubernetesAccountSpec):

    server = "127.0.0.1"
    account_type = KUBERNETES.ACCOUNT.VANILLA
    port = 9440
    auth = KubernetesAuth.client_certificate(
        client_key="client_key", client_certificate="client_certificate"
    )


class K8sClientCertAccount(Account):

    provider_type = PROVIDER.ACCOUNT.KUBERNETES
    spec = K8sSpec
