import json

from calm.dsl.builtins import (
    Blueprint,
    Profile,
    Deployment,
    Substrate,
    Package,
    Service,
    dynamic_cred,
    ref,
    read_local_file,
    Ref,
    Metadata,
)
from calm.dsl.builtins import CalmTask, CalmVariable, action, parallel, provider_spec


DNS_SERVER = read_local_file(".tests/dns_server")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
EXISTING_VM_IP = DSL_CONFIG["EXISTING_MACHINE"]["IP_1"]
DEFAULT_CRED_USERNAME = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["LINUX"]["USERNAME"]
CRED_PASSWORD = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["LINUX"]["PASSWORD"]
CRED_PROVIDER = "HashiCorpVault_Cred_Provider"
SECRET_PATH = "nutanix"


DefaultCred = dynamic_cred(
    DEFAULT_CRED_USERNAME,
    Ref.Account(name=CRED_PROVIDER),
    variable_dict={"path": SECRET_PATH},
    name="default cred",
    default=True,
)


class AppService(Service):
    ENV = CalmVariable.WithOptions.Predefined.string(
        ["DEV", "PROD"], default="DEV", is_mandatory=True, runtime=True
    )

    @action
    def __start__():
        CalmTask.Exec.ssh(name="Task1", script="echo 'Service start in ENV=@@{ENV}@@'")

    @action
    def __stop__():
        CalmTask.Exec.ssh(name="Task1", script="echo 'Service stop in ENV=@@{ENV}@@'")

    @action
    def sample_action():
        with parallel():
            CalmTask.Exec.ssh(
                name="Task1", script="echo 'Sample parallel Task 1'\ndate"
            )
            CalmTask.Exec.ssh(
                name="Task2", script="echo 'Sample parallel Task 2'\ndate"
            )


class AppPackage(Package):
    services = [ref(AppService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="Task1", script="echo 'Sample Install script'", cred=ref(DefaultCred)
        )


class ExistingVM(Substrate):
    """CentOS VM"""

    provider_type = "EXISTING_VM"
    provider_spec = provider_spec({"address": EXISTING_VM_IP})
    readiness_probe = {
        "disabled": False,
        "delay_secs": "10",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }

    @action
    def __pre_create__():
        CalmTask.Exec.escript.py3(
            name="Pre Create Task", script="print ('Pre Create task for ExistingVM')"
        )


class AppDeployment(Deployment):

    packages = [ref(AppPackage)]
    substrate = ref(ExistingVM)
    min_replicas = "@@{replica_count}@@"
    max_replicas = "@@{calm_int(replica_count) + 1}@@"


class DefaultProfile(Profile):

    nameserver = CalmVariable("1.1.1.1", label="Local DNS resolver")
    replica_count = CalmVariable.WithOptions.Predefined.int(
        ["1", "2"], default="1", validate_regex=True, runtime=True
    )
    deployments = [AppDeployment]

    @action
    def sample_profile_action():
        CalmTask.Exec.ssh(name="Task 1", script="echo 'Hi'", target=ref(AppService))
        AppService.sample_action(name="Call Runbook for sample_action")
        CalmTask.Scaling.scale_out(1, target=ref(AppDeployment), name="Scale out Task")
        CalmTask.Scaling.scale_in(1, target=AppDeployment, name="Scale in Task")


class ExampleBlueprint(Blueprint):
    """Example Blueprint"""

    credentials = [DefaultCred]
    services = [AppService]
    packages = [AppPackage]
    substrates = [ExistingVM]
    profiles = [DefaultProfile]


class BpMetadata(Metadata):

    project = Ref.Project("test_dyn_cred_project")


def main():
    print(ExampleBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
