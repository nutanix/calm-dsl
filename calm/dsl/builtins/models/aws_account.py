from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle

from .account import AccountDataType


LOG = get_logging_handle(__name__)


class AwsAccountDataType(AccountDataType):
    __schema_name__ = "AwsAccountData"
    __openapi_type__ = "aws_account_data"

    __provider_type__ = "aws"


class AwsAccountDataValidator(PropertyValidator, openapi_type="aws_account_data"):
    __default__ = None
    __kind__ = AwsAccountDataType


def aws_account_data(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AwsAccountDataType(name, bases, kwargs)


AwsAccountData = aws_account_data()
