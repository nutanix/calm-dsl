from calm.dsl.constants import PROVIDER
from calm.dsl.builtins import Account, AwsAccountSpec


class AwsSpec(AwsAccountSpec):

    access_key_id = "aws_access_key"
    secret_access_key = "aws_secret_access_key"
    regions = [
        {
            "name": "us_east1",  # key
            "images": [
                {
                    "image_id": "ami-07104d8cc199a2836",
                    "name": "fedora-coreos-30.20190827.dev.1-hvm",  # key
                    "root_device_name": "/dev/xvda",
                },
                {
                    "image_id": "ami-0f9a9e1765ca51e81",
                    "name": "fedora-coreos-31.20200331.20.0-hvm",  # key
                    "root_device_name": "/dev/xvda",
                },
                {
                    "image_id": "ami-0e2c906d7e70265b2",
                    "name": "fedora-coreos-32.20200605.20.0",  # keys
                    "root_device_name": "/dev/xvda",
                },
            ],
        }
    ]


class AwsAccount(Account):
    provider_type = PROVIDER.ACCOUNT.AWS
    spec = AwsSpec


print(AwsAccount.json_dumps(pprint=True))
