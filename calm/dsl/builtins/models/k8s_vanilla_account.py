import sys

from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import PROVIDER, PROVIDER_RESOURCE
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


# K8S vanilla account


class KubernetesVanillaAccountSpecType(AccountSpecType):
    __schema_name__ = "KubernetesVanillaAccountSpec"
    __openapi_type__ = "kubernetes_vanilla_account_spec"

    __provider_type__ = PROVIDER.KUBERNETES
    __resource_type__ = PROVIDER_RESOURCE.KUBERNETES.VANILLA


class KubernetesVanillaAccountSpecValidator(
    PropertyValidator, openapi_type="kubernetes_vanilla_account_spec"
):
    __default__ = None
    __kind__ = KubernetesVanillaAccountSpecType


def vanilla_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return KubernetesVanillaAccountSpecType(name, bases, kwargs)


VanillaAccountSpec = vanilla_account_spec()
