from calm.dsl.builtins import Account, VanillaAccountSpec
from calm.dsl.constants import PROVIDER
from calm.dsl.builtins import Auth


class K8sSpec(VanillaAccountSpec):

    server = "127.0.0.1"
    port = 9440
    auth = Auth.Kubernetes.basic(username="username", password="password")


class K8sBasicAuthAccount(Account):

    provider_type = PROVIDER.KUBERNETES
    spec = K8sSpec
