from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.log import get_logging_handle
from calm.dsl.constants import PROVIDER


LOG = get_logging_handle(__name__)


class AwsAccountSpecType(AccountSpecType):
    __schema_name__ = "AwsAccountSpec"
    __openapi_type__ = "aws_account_spec"

    __provider_type__ = PROVIDER.ACCOUNT.AWS


class AwsAccountDataValidator(PropertyValidator, openapi_type="aws_account_spec"):
    __default__ = None
    __kind__ = AwsAccountSpecType


def aws_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AwsAccountSpecType(name, bases, kwargs)


AwsAccountSpec = aws_account_spec()
