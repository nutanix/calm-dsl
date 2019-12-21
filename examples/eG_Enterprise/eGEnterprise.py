""""
eG Enterprise is an end-to-end performance management solution for Nutanix hyper-converged infrastructure.
Using correlative intelligence and machine learning, eG Enterprise understands the interdependencies between the Nutanix platform and application workloads,
helping IT identify the root cause of performance slowdowns.
"""

from calm.dsl.builtins import ref, basic_cred, CalmTask
from calm.dsl.builtins import action
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec, read_local_file


ADMIN_PASSWD = read_local_file("admin_passwd")

DefaultCred = basic_cred("administrator", ADMIN_PASSWD, name="LOCAL", default=True)


class eGenterprise(Service):
    """eG Enterprise Service"""


class eGAgentPackage(Package):
    """Install eG agent"""

    services = [ref(eGenterprise)]

    @action
    def __install__():
        CalmTask.Exec.powershell(
            name="eGAgentPackage",
            filename="scripts/eGAgent_Installation.ps1",
            cred=ref(DefaultCred),
        )


class eGenterpriseSubstrate(Substrate):
    os_type = "Windows"
    provider_spec = read_provider_spec("ahv_spec_win.yaml")
    readiness_probe = {
        "disabled": False,
        "delay_secs": "90",
        "connection_type": "POWERSHELL",
        "connection_port": 5985,
        "credential": ref(DefaultCred),
    }


class eGenterpriseDeployment(Deployment):
    packages = [ref(eGAgentPackage)]
    substrate = ref(eGenterpriseSubstrate)
    min_replicas = "1"
    max_replicas = "1"


class Nutanix(Profile):
    EXE_FILE_URL = CalmVariable.Simple(
        "http://download.eginnovations.com/nutanix/eGAgent_win2012_x64.exe",
        label="eG agent exe file public url",
        is_mandatory=True,
        runtime=True,
    )
    ISS_FILE_URL = CalmVariable.Simple(
        "http://download.eginnovations.com/nutanix/eGAgentInstall.iss",
        label="eG agent IIS file public url",
        is_mandatory=True,
        runtime=True,
    )
    URL_USERNAME = CalmVariable.Simple(
        "nutanix",
        label="Username for the URL to downalod the files",
        is_mandatory=True,
        runtime=True,
    )
    URL_PASSWORD = CalmVariable.Simple(
        "nutanixdemo",
        label="Password for the URL to downalod the files",
        is_mandatory=True,
        runtime=True,
    )
    UNINSTALL_ISS_FILE = CalmVariable.Simple(
        "http://download.eginnovations.com/nutanix/eGAgentUninstall.iss",
        label="ISS file public url for the uninstallation",
        is_mandatory=True,
        runtime=True,
    )

    deployments = [eGenterpriseDeployment]

    @action
    def NICK_CONFIGURATION():
        """This Nick configuration action is required to map customer details uniquely with egenterprise."""
        NICK_NAME = CalmVariable.Simple.string(  # noqa
            "unique",
            label="This is used for uniquely ",
            is_mandatory=True,
            runtime=True,
        )
        CalmTask.Exec.powershell(
            name="NICK_FILE_Creation",
            filename="scripts/NICK_CONFIGURATION.ps1",
            target=ref(eGenterprise),
            cred=ref(DefaultCred),
        )


class eGenterpriseBlueprint(Blueprint):
    """*Access the eg agent by login into the [Target](EgEnterpriseService.address) machine"""

    profiles = [Nutanix]
    services = [eGenterprise]
    substrates = [eGenterpriseSubstrate]
    packages = [eGAgentPackage]
    credentials = [DefaultCred]


def main():
    print(eGenterpriseBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
