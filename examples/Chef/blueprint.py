from calm.dsl.builtins import basic_cred
from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import action, read_local_file


SSH_PASSWD = read_local_file("passwd")
CHEF_PASSWD = read_local_file("passwd")


class ChefDeployment(SimpleDeployment):

    provider_spec = read_provider_spec("ahv_spec.yaml")

    @action
    def __install__():
        Task.Exec.ssh(name="Install Chef", filename="scripts/Install.sh")

    @action
    def __create__():
        Task.Exec.ssh(name="Configure", filename="scripts/Configure.sh")


class ChefBlueprint(SimpleBlueprint):

    CHEF_SERVER_VERSION = Var.Simple.string("12.17.5", is_mandatory=True, runtime=True)
    CHEF_USERNAME = Var.Simple.string("chefadmin", is_mandatory=True, runtime=True)
    CHEF_PASSWORD = Var.Simple.Secret(
        CHEF_PASSWD, is_hidden=True, is_mandatory=True, runtime=True
    )
    CHEF_ORG_NAME = Var.Simple.string("calm-dev", is_mandatory=True, runtime=True)
    FIRST_NAME = Var.Simple.string("first_name", is_mandatory=True, runtime=True)
    MIDDLE_NAME = Var.Simple.string("middle_name", is_mandatory=True, runtime=True)
    LAST_NAME = Var.Simple.string("last_name", is_mandatory=True, runtime=True)
    EMAIL = Var.Simple.string("user@example.com", is_mandatory=True, runtime=True)
    CHEF_ORG_FULL_NAME = Var.Simple.string("example", is_mandatory=True, runtime=True)

    credentials = [basic_cred("centos", SSH_PASSWD, name="CENTOS", default=True)]
    deployments = [ChefDeployment]


def main():
    print(ChefBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
