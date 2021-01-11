from calm.dsl.constants import PROVIDER
from calm.dsl.builtins import Account, AwsC2sAccountSpec


class AwsSpec(AwsC2sAccountSpec):

    c2s_account_address = "c2s_account_address"
    client_certificate = "client_certificate"
    client_key = "client_key"
    role = "role"
    mission = "mission"
    agency = "agency"
    regions = [
        {
            "name": "us-gov-west-1",
        }
    ]


class AwsC2sAccount(Account):
    provider_type = PROVIDER.AWS.C2S
    spec = AwsSpec
