from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.log import get_logging_handle
from calm.dsl.constants import PROVIDER, PROVIDER_RESOURCE


LOG = get_logging_handle(__name__)


class AwsEc2AccountSpecType(AccountSpecType):
    __schema_name__ = "AwsEc2AccountSpec"
    __openapi_type__ = "aws_ec2_account_spec"

    __provider_type__ = PROVIDER.AWS
    __resource_type__ = PROVIDER_RESOURCE.AWS.EC2

    def compile(cls):
        """returns the compiled payload for aws account spec"""

        cdict = super().compile()
        password = cdict.pop("secret_access_key", None)
        cdict["secret_access_key"] = {
            "attrs": {"is_secret_modified": True},
            "value": password,
        }

        return cdict


class AwsEc2AccountSpecValidator(
    PropertyValidator, openapi_type="aws_ec2_account_spec"
):
    __default__ = None
    __kind__ = AwsEc2AccountSpecType


def aws_ec2_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AwsEc2AccountSpecType(name, bases, kwargs)


AwsEc2AccountSpec = aws_ec2_account_spec()
