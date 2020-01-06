"""
Hadoop Blueprint

"""

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import action
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec, read_local_file


CENTOS_PASSWD = read_local_file("passwd")

DefaultCred = basic_cred("centos", CENTOS_PASSWD, name="default cred", default=True)


class Hadoop_Master(Service):
    """Hadoop_Master service"""

    @action
    def __create__():
        CalmTask.Exec.ssh(name="ConfigureMaster", filename="scripts/ConfigureMaster.sh")

    @action
    def __start__():
        CalmTask.Exec.ssh(
            name="StartMasterServices", filename="scripts/StartMasterServices.sh"
        )


class Hadoop_Slave(Service):
    """Hadoop_Slave service"""

    @action
    def __create__():
        CalmTask.Exec.ssh(name="ConfigureSlave", filename="scripts/ConfigureSlave.sh")

    @action
    def __start__():
        CalmTask.Exec.ssh(
            name="StartSlaveServices", filename="scripts/StartSlaveServices.sh"
        )


class Hadoop_Master_Package(Package):
    """Hadoop Master package"""

    services = [ref(Hadoop_Master)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask", filename="scripts/master_PackageInstallTask.sh"
        )


class Hadoop_Slave_Package(Package):
    """Hadoop Slave package"""

    services = [ref(Hadoop_Slave)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask", filename="scripts/slave_PackageInstallTask.sh"
        )


class Hadoop_Master_AHV(Substrate):
    """Hadoop Master Substrate"""

    provider_spec = read_provider_spec("ahv_spec.yaml")
    provider_spec.spec["name"] = "Hadoop_Master-@@{calm_array_index}@@-@@{calm_time}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class Hadoop_Slave_AHV(Substrate):
    """Hadoop Slave Substrate"""

    provider_spec = read_provider_spec("ahv_spec.yaml")
    provider_spec.spec["name"] = "Hadoop_Slave-@@{calm_array_index}@@-@@{calm_time}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class Hadoop_Master_Deployment(Deployment):
    """Hadoop Master Deployment"""

    packages = [ref(Hadoop_Master_Package)]
    substrate = ref(Hadoop_Master_AHV)


class Hadoop_Slave_Deployment(Deployment):
    """Hadoop Slave Deployment"""

    min_replicas = "2"
    max_replicas = "5"

    packages = [ref(Hadoop_Slave_Package)]
    substrate = ref(Hadoop_Slave_AHV)


class Nutanix(Profile):
    """Hadoop Profile"""

    deployments = [Hadoop_Master_Deployment, Hadoop_Slave_Deployment]

    @action
    def ScaleOutSlaves():
        COUNT = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_out(
            "@@{COUNT}@@", target=ref(Hadoop_Slave_Deployment), name="ScaleOutSlaves"
        )

    @action
    def ScaleInSlaves():
        COUNT = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_in(
            "@@{COUNT}@@", target=ref(Hadoop_Slave_Deployment), name="ScaleInSlaves"
        )


class HadoopDslBlueprint(Blueprint):
    """* [Hadoop Master Name Node Dashboard](http://@@{Hadoop_Master.address}@@:50070)
* [Hadoop Master Data Node Dashboard](http://@@{Hadoop_Master.address}@@:8088)
    """

    credentials = [DefaultCred]
    services = [Hadoop_Master, Hadoop_Slave]
    packages = [Hadoop_Master_Package, Hadoop_Slave_Package]
    substrates = [Hadoop_Master_AHV, Hadoop_Slave_AHV]
    profiles = [Nutanix]


def main():
    print(HadoopDslBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
