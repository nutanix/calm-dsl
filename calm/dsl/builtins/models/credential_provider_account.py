from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY

LOG = get_logging_handle(__name__)

# CredentialProvider


class CredentialProviderAccountType(EntityType):
    __schema_name__ = "CredAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.CREDENTIAL_PROVIDER


class CredAccountTypeValidator(
    PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.CREDENTIAL_PROVIDER
):
    __default__ = None
    __kind__ = CredentialProviderAccountType


def credential_provider_account(**kwargs):

    name = kwargs.pop("name", None)
    bases = (Entity,)
    return CredentialProviderAccountType(name, bases, kwargs)


CredAccount = credential_provider_account()
