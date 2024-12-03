from calm.dsl.builtins import Account, AccountResources, Ref

# Provider with name "HelloProvider" should already exist
PROVIDER_NAME = "HelloProvider"


class HelloAccount(Account):
    """Account corresponding to HelloProvider"""

    type = PROVIDER_NAME
    resources = AccountResources.CustomProvider(
        provider=Ref.Provider(PROVIDER_NAME),
        variable_dict={  # Keys of this dict are variable names from the list of provider's [auth_schema + endpoint_schema]
            "server_ip": "10.10.01.231",
            "port_number": "9440",
            "username": "uzumaki.naruto",
            "password": "rasengannnn",
            "provider_var": "new_val",
        },
    )
