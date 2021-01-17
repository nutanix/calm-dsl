from calm.dsl.builtins import Account, VanillaAccountSpec, Auth
from calm.dsl.constants import PROVIDER


class K8sSpec(VanillaAccountSpec):

    server = "127.0.0.1"
    port = 9440
    auth = Auth.Kubernetes.ca_certificate(
        client_key="client_key",
        ca_certificate="ca_certificate",
        client_certificate="client_certificate",
    )


class K8sCaCertAuthAccount(Account):

    provider_type = PROVIDER.KUBERNETES
    spec = K8sSpec
