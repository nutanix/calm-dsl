from .entity import EntityType, Entity

from calm.dsl.constants import ACCOUNT
from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator

LOG = get_logging_handle(__name__)

# CredentialProvider Resources


class CredentialProviderResourcesType(EntityType):
    __schema_name__ = "CredAccountResources"
    __openapi_type__ = "app_credential_provider_resources"


class CredAccountResourcesTypeValidator(
    PropertyValidator, openapi_type="app_credential_provider_resources"
):
    __default__ = None
    __kind__ = CredentialProviderResourcesType


def credential_provider_resources(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return CredentialProviderResourcesType(name, bases, kwargs)


CredAccountResources = credential_provider_resources()
