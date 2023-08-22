import sys
from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY

LOG = get_logging_handle(__name__)

# Kubernetes Vanilla Account


class K8sVanillaAccountType(EntityType):
    __schema_name__ = "K8sVanillaAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.K8S_VANILLA


class K8sVanillaAccountValidator(
    PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.K8S_VANILLA
):
    __default__ = None
    __kind__ = K8sVanillaAccountType


def k8s_vanilla_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return K8sVanillaAccountType(name, bases, kwargs)


K8sVanillaAccountData = k8s_vanilla_account()
