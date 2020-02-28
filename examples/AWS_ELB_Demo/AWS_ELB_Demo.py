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


# Local Data
CENTOS_KEY = read_local_file("mpi_ssh_key")
ROOT_PASSWD = read_local_file("passwd")
MYSQL_PASSWD = read_local_file("mysql_passwd")
WP_PASSWD = read_local_file("wp_passwd")
AWS_PROVIDER_ACCESS_KEY_ID = read_local_file("aws_access_key_id")
AWS_PROVIDER_SECRET_ACCESS_KEY = read_local_file("aws_secret_access_key")

# Creds
CENTOS = basic_cred("centos", CENTOS_KEY, name="CENTOS", type="KEY", default=True)
ROOT = basic_cred("root", ROOT_PASSWD, name="root")


class MYSQL(Service):
    """MySql Service"""

    @action
    def __create__():
        CalmTask.Exec.ssh(
            name="CreateWordPressDB",
            filename="scripts/CreateWordPressDB.sh",
            cred=ref(CENTOS),
        )


class APACHE_PHP(Service):
    """Apache PHP Service"""

    @action
    def __create__():
        CalmTask.Exec.ssh(
            name="ConfigureWordpress",
            filename="scripts/ConfigureWordpress.sh",
            cred=ref(CENTOS),
        )

    dependencies = [ref(MYSQL)]


class AWS_ELB(Service):
    """Apache PHP Service"""

    dependencies = [ref(APACHE_PHP)]

    WP_ELB = CalmVariable.WithOptions.Predefined.string([""])
    TG_ID = CalmVariable.WithOptions.Predefined.string([""])


class MYSQL_AWS_Package(Package):
    """MySql AWS Package"""

    services = [ref(MYSQL)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask", filename="scripts/MySqlPackageInstallTask.sh"
        )


class APACHE_PHP_Package(Package):
    """APACHE PHP Package"""

    services = [ref(APACHE_PHP)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask", filename="scripts/ApachePHPPackageInstallTask.sh"
        )


class CreateELBPackage(Package):
    """Create ELB Package"""

    services = [ref(AWS_ELB)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PythonLibraryInstallTask",
            filename="scripts/PythonLibraryInstallTask.sh",
            cred=ref(ROOT),
        )
        CalmTask.SetVariable.ssh(
            name="PackageInstallTask",
            filename="scripts/CreateELBPackageInstallTask.sh",
            variables=["WP_ELB", "TG_ID"],
            cred=ref(ROOT),
        )


class MYSQL_AWS(Substrate):
    """ MySql AWS Substrate """

    provider_type = "AWS_VM"
    provider_spec = read_provider_spec("aws_mysql_spec.yaml")


class AWS_WORDPRESS(Substrate):
    """AWS Wordpress Substrate"""

    provider_type = "AWS_VM"
    provider_spec = read_provider_spec("aws_wordpress_spec.yaml")


class CreateELBSubstrate(Substrate):
    """ Existing Machine VM3 Substrate """

    provider_type = "EXISTING_VM"
    provider_spec = read_provider_spec("vm3_em_spec.yaml")

    readiness_probe = {"credential": ref(ROOT)}


class MySqlDeployment(Deployment):
    """MySql Deployment"""

    packages = [ref(MYSQL_AWS_Package)]
    substrate = ref(MYSQL_AWS)


class ApachePHPDeployment(Deployment):
    """Apache PHP Deployment"""

    min_replicas = "2"
    max_replicas = "4"

    packages = [ref(APACHE_PHP_Package)]
    substrate = ref(AWS_WORDPRESS)


class CreateELBDeployment(Deployment):
    """Create ELB Deployment"""

    packages = [ref(CreateELBPackage)]
    substrate = ref(CreateELBSubstrate)


class AWSProfile(Profile):
    """AWS Profile"""

    deployments = [MySqlDeployment, ApachePHPDeployment, CreateELBDeployment]

    MYSQL_PASSWORD = CalmVariable.Simple.Secret(
        MYSQL_PASSWD, is_mandatory=False, runtime=True
    )
    WP_DB_USER = CalmVariable.Simple("wordpress")
    WP_DB_PASSWORD = CalmVariable.Simple.Secret(
        WP_PASSWD, is_mandatory=False, runtime=True
    )
    AWS_ACCESS_KEY_ID = CalmVariable.Simple.Secret(
        AWS_PROVIDER_ACCESS_KEY_ID
    )
    AWS_SECRET_ACCESS_KEY = CalmVariable.Simple.Secret(
        AWS_PROVIDER_SECRET_ACCESS_KEY
    )

    @action
    def ScaleOut():
        """This action will scale out wordpress app vms by given count"""

        COUNT = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_out(
            "@@{COUNT}@@", target=ref(ApachePHPDeployment), name="Scale Out App"
        )
        CalmTask.Exec.ssh(
            name="Scale Out",
            filename="scripts/ProfileScaleOutTask.sh",
            cred=ref(ROOT),
            target=ref(AWS_ELB),
        )

    @action
    def ScaleIn():
        """This action will scale in wordpress app vms by given count"""

        COUNT = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_in(
            "@@{COUNT}@@", target=ref(ApachePHPDeployment), name="Scale Out App"
        )
        CalmTask.Exec.ssh(
            name="Scale In",
            filename="scripts/ProfileScaleInTask.sh",
            cred=ref(ROOT),
            target=ref(AWS_ELB),
        )


class DemoAWSELB(Blueprint):
    """* [Wordpress](http://@@{AWS_ELB.WP_ELB}@@)"""

    credentials = [CENTOS, ROOT]
    services = [MYSQL, APACHE_PHP, AWS_ELB]
    packages = [MYSQL_AWS_Package, APACHE_PHP_Package, CreateELBPackage]
    substrates = [MYSQL_AWS, AWS_WORDPRESS, CreateELBSubstrate]
    profiles = [AWSProfile]


def main():
    print(DemoAWSELB.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
