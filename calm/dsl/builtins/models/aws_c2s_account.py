from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY

LOG = get_logging_handle(__name__)

# AWS Account


class AwsC2SAccountType(EntityType):
    __schema_name__ = "AwsC2SAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.AWS_C2S

    def compile(cls):
        cdict = super().compile()

        client_certificate = cdict.pop("client_certificate", None)
        cdict["client_certificate"] = {
            "attrs": {"is_secret_modified": True},
            "value": client_certificate,
        }

        client_key = cdict.pop("client_key", None)
        cdict["client_key"] = {
            "attrs": {"is_secret_modified": True},
            "value": client_key,
        }

        return cdict


class AwsC2SAccountValidator(
    PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.AWS_C2S
):
    __default__ = None
    __kind__ = AwsC2SAccountType


def aws_c2s_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return AwsC2SAccountType(name, bases, kwargs)


AwsC2SAccountData = aws_c2s_account()
