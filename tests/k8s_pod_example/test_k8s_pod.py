"""
Calm DSL .NEXT demo

"""

from calm.dsl.builtins import ref, basic_cred, CalmVariable, CalmTask, action
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint, PODDeployment
from calm.dsl.builtins import read_provider_spec, read_spec, read_local_file

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server")


class MySQLService(Service):
    """Sample mysql service"""

    ENV = CalmVariable.Simple("DEV")


class MySQLPackage(Package):
    """Example package with variables, install tasks and link to service"""

    foo = CalmVariable.Simple("bar")
    services = [ref(MySQLService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")


class AHVVMforMySQL(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")


class MySQLDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(MySQLPackage)]
    substrate = ref(AHVVMforMySQL)


class RedisService(Service):
    pass


class DiscourseService(Service):
    pass


class K8SDeployment1(PODDeployment):
    """ Sample K8S Deployment """

    containers = [RedisService, DiscourseService]
    deployment_spec = read_spec("specs/deployment1.yaml")
    service_spec = read_spec("specs/service1.yaml")

    # dependencies to indicate provisioning of K8sDeployment1 is dependent of the MySQLDeployment creation
    dependencies = [ref(MySQLDeployment)]


class PHPService(Service):
    """Sample PHP service with a custom action"""

    # Dependency to indicate PHP service is dependent on SQL service being up
    dependencies = [ref(MySQLService)]

    @action
    def test_action():

        blah = CalmVariable.Simple("2")  # noqa
        CalmTask.Exec.ssh(name="Task2", script='echo "Hello"')
        CalmTask.Exec.ssh(name="Task3", script='echo "Hello again"')


class PHPPackage(Package):
    """Example PHP package with custom install task"""

    foo = CalmVariable.Simple("baz")
    services = [ref(PHPService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task4", script="echo @@{foo}@@")


class AHVVMforPHP(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")


class PHPDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(PHPPackage)]
    substrate = ref(AHVVMforPHP)

    # Dependency indicates PHP Deployment will be created once Provision Kubernetes happened
    dependencies = [ref(K8SDeployment1)]


class MailService(Service):
    pass


class K8SDeployment2(PODDeployment):
    """ Sample K8S Deployment """

    containers = [MailService]
    deployment_spec = read_spec("specs/deployment2.yaml")
    service_spec = read_spec("specs/service2.yaml")

    # Dependency indicates Provision of K8sDeployment will happen after PHP Deployment is created
    dependencies = [ref(PHPDeployment)]


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple(DNS_SERVER, label="Local DNS resolver")
    deployments = [MySQLDeployment, PHPDeployment, K8SDeployment1, K8SDeployment2]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(MySQLService))
        PHPService.test_action(name="Task6")


class K8SBlueprint(Blueprint):
    """Calm Kubernetes POD Support demo"""

    credentials = [basic_cred(CRED_USERNAME, CRED_PASSWORD, default=True)]
    services = [MySQLService, PHPService, RedisService, DiscourseService, MailService]
    packages = [MySQLPackage, PHPPackage]
    substrates = [AHVVMforMySQL, AHVVMforPHP]
    profiles = [DefaultProfile]


def main():
    print(K8SBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
