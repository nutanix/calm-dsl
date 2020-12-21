from calm.dsl.builtins import Account, AhvAccountSpec


class AhvSpec(AhvAccountSpec):

    server = "ahv_pc_ip"
    username = "username"
    password = "password"
    port = 9440


class AhvAccount(Account):

    provider_type = "nutanix_pc"  # Replace by constant
    spec = AhvSpec


print(AhvAccount.json_dumps(pprint=True))
