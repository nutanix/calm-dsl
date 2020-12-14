from calm.dsl.builtins import Account, AccountResource, AhvAccountData, account_resource


class AhvData(AhvAccountData):

    server = "ahv_pc_ip"
    username = "username"
    password = "password"
    port = 9440


class AhvAccount(Account):
    name = "Ahv Account"
    resources = account_resource(type="nutanix_pc", data=AhvData)


print(AhvAccount.json_dumps(pprint=True))
