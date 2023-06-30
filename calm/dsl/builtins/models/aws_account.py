from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY

LOG = get_logging_handle(__name__)

# AWS Account


class AwsAccountType(EntityType):
    __schema_name__ = "AwsAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.AWS

    def compile(cls):
        cdict = super().compile()
        secret_access_key_value = cdict.pop("secret_access_key", "")
        cdict["secret_access_key"] = {
            "value": secret_access_key_value,
            "attrs": {"is_secret_modified": True},
        }
        return cdict


class AwsAccountValidator(PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.AWS):
    __default__ = None
    __kind__ = AwsAccountType


def aws_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return AwsAccountType(name, bases, kwargs)


AwsAccountData = aws_account()
