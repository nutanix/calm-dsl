from calm.dsl.builtins import Account, KubernetesAccountSpec, KubernetesAuth
from calm.dsl.constants import PROVIDER


class K8sSpec(KubernetesAccountSpec):

    server = "127.0.0.1"
    type = "vanilla"
    port = 9440
    auth = KubernetesAuth.basic(username="username", password="password")


class K8sBasicAuthAccount(Account):

    provider_type = PROVIDER.ACCOUNT.KUBERNETES
    spec = K8sSpec


print(K8sBasicAuthAccount.json_dumps(pprint=True))
