from calm.dsl.builtins import basic_cred, CalmTask, action
from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec, read_local_file


ADMIN_PASSWD = read_local_file("admin_passwd")

DefaultCred = basic_cred("administrator", ADMIN_PASSWD, name="LOCAL", default=True)


class MSSQLDeployment(SimpleDeployment):

    provider_spec = read_provider_spec("ahv_spec.yaml")
    os_type = "Windows"

    @action
    def __install__():
        CalmTask.Exec.powershell(
            name="PreRequisite", filename="scripts/PreRequisite.ps1"
        )
        CalmTask.Exec.powershell(name="Install MSSQL", filename="scripts/Install.ps1")
        CalmTask.Exec.powershell(
            name="Open Firewall", filename="scripts/OpenFirewall.ps1"
        )


class MSSQLBlueprint(SimpleBlueprint):

    credentials = [DefaultCred]
    deployments = [MSSQLDeployment]


def main():
    print(MSSQLBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
