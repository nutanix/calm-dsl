from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.log import get_logging_handle
from calm.dsl.constants import PROVIDER


LOG = get_logging_handle(__name__)


class AwsC2sAccountSpecType(AccountSpecType):
    __schema_name__ = "AwsC2sAccountSpec"
    __openapi_type__ = "aws_c2s_account_spec"

    __provider_type__ = PROVIDER.AWS.C2S

    def compile(cls):
        """returns the compiled payload for aws account spec"""

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


class AwsC2sAccountSpecValidator(
    PropertyValidator, openapi_type="aws_c2s_account_spec"
):
    __default__ = None
    __kind__ = AwsC2sAccountSpecType


def aws_c2s_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AwsC2sAccountSpecType(name, bases, kwargs)


AwsC2sAccountSpec = aws_c2s_account_spec()
