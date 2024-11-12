# flake8: noqa
# pylint: skip-file
from calm.dsl.builtins import Account, AccountResources, Ref, read_local_file

# Provider with name "DSL_AWSProvider" should already exist
PROVIDER_NAME = "DSL_AWSProvider"

CloudProvider_AWSProvider_account_variable_secret_access_key = read_local_file(
    "CloudProvider_AWSProvider_account_variable_secret_access_key"
)


class HelloAccount(Account):
    """Account corresponding to DSL_AWSProvider"""

    type = PROVIDER_NAME
    resources = AccountResources.CustomProvider(
        provider=Ref.Provider(PROVIDER_NAME),
        variable_dict={  # Keys of this dict are variable names from the list of provider's [auth_schema + endpoint_schema]
            "access_key_id": "AKIA2LDLYW6I5ZSKVMAJ",
            "secret_access_key": CloudProvider_AWSProvider_account_variable_secret_access_key,
        },
    )
