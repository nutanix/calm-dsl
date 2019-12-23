from calm.dsl.builtins import ref, basic_cred, CalmTask
from calm.dsl.builtins import CalmVariable, action
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec
from calm.dsl.builtins import read_file, read_local_file


# Local Config
CENTOS_PASSWORD = read_local_file("passwd")
REDIS_PASSWORD = read_local_file("passwd")

DefaultCred = basic_cred("centos", CENTOS_PASSWORD, name="CENTOS", default=True)


class RedisMaster(Service):
    """Redis Master Service"""
    pass


class MasterPackage(Package):
    """Redis MasterPackage"""

    services = [ref(RedisMaster)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Master_Package.sh",
            cred=ref(DefaultCred),
        )


class RedisMasterSubstrate(Substrate):
    provider_spec = read_provider_spec("ahv_spec_centos.yaml")
    provider_spec.spec["name"] = "Redis_Master-@@{calm_array_index}@@-@@{calm_random}@@"
    os_type = "Linux"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class RedisMasterDeployment(Deployment):
    packages = [ref(MasterPackage)]
    substrate = ref(RedisMasterSubstrate)
    min_replicas = "1"
    max_replicas = "1"


class RedisSlave(Service):
    """Redis Slave Service"""

    dependencies = [ref(RedisMasterDeployment)]


class SlavePackage(Package):
    """Redis SlavePackage"""

    services = [ref(RedisSlave)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Slave_Package.sh",
            cred=ref(DefaultCred),
        )


class RedisSlaveSubstrate(Substrate):
    os_type = "Linux"
    provider_spec = read_provider_spec("ahv_spec_centos.yaml")
    provider_spec.spec["name"] = "Redis_Slave-@@{calm_array_index}@@-@@{calm_random}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class RedisSlaveDeployment(Deployment):
    packages = [ref(SlavePackage)]
    substrate = ref(RedisSlaveSubstrate)
    min_replicas = "2"
    max_replicas = "4"


class Nutanix(Profile):
    """docstring for Nutanix"""

    REDIS_CONFIG_PASSWORD = CalmVariable.Simple.Secret(
        REDIS_PASSWORD,
        label="Redis Configuration Password",
        is_mandatory=True,
        runtime=True,
    )

    deployments = [RedisMasterDeployment, RedisSlaveDeployment]

    @action
    def ScaleOut():
        """This action will scale out Redis slaves by given scale out count"""
        Scaleout = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_out(
            "@@{Scaleout}@@", target=ref(RedisSlaveDeployment), name="Scale out Slave"
        )

    @action
    def ScaleIn():
        """This action will scale in Redis slaves by given scale in count"""
        ScaleIn = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_in(
            "@@{ScaleIn}@@", target=ref(RedisSlaveDeployment), name="Scale in Slave"
        )


class RedisBlueprint(Blueprint):
    """Accessibility:
    * redis-cli from master host"""

    profiles = [Nutanix]
    services = [RedisMaster, RedisSlave]
    substrates = [RedisMasterSubstrate, RedisSlaveSubstrate]
    packages = [MasterPackage, SlavePackage]
    credentials = [DefaultCred]


def main():
    print(RedisBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
