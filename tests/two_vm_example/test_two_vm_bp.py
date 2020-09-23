"""
Sample single vm example to convert python dsl to calm v3 api spec

"""
import sys

from calm.dsl.builtins import port, ref, setvar, basic_cred
from calm.dsl.builtins import Port, Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec, CalmVariable, read_local_file

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server_two_vm_example")
MYSQL_PORT = read_local_file(".tests/mysql_port")
# Setting the recursion limit to max for
sys.setrecursionlimit(100000)


class MySQLService(Service):
    """Sample mysql service with inline port definition"""

    ports = [port(target_port=MYSQL_PORT)]


class MySQLPackage(Package):
    """Example package with variables and link to service"""

    # use var_name = vartype(attrs) to define a package variable
    ENV = CalmVariable.Simple("DEV")

    # Services to configure after package is installed.
    services = [ref(MySQLService)]


class PHPPort(Port):
    """Sample Port definition"""

    target_port = "80"


class PHPService(Service):
    """Sample PHP service using Service as parent class
    with previously defined port.
    """

    # use var_name = vartype(attrs) to define a service variable
    sample_string_var = CalmVariable.Simple("hello world!")

    ports = [PHPPort]

    # Dependency to indicate PHP service is dependent on SQL service being up
    dependencies = [ref(MySQLService)]


class PHPPackage(Package):
    """Example PHP package using Package as parent class"""

    services = [ref(PHPService)]


class AHVMedVM(Substrate):
    """Medium size AHV VM config given by reading a spec file"""

    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")


class AHVMedVMForPHP(Substrate):
    """Medium size AHV VM config given by reading a spec file"""

    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")


class MySQLDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(MySQLPackage)]
    substrate = ref(AHVMedVM)


class PHPDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(PHPPackage)]
    substrate = ref(AHVMedVMForPHP)


class NxProfile(Profile):
    """Sample application profile with variables"""

    # use var_name = vartype(attrs) to define a variable at class level
    DNS_Server = CalmVariable.Simple(DNS_SERVER, label="Local DNS resolver")

    # Use setvar(name, attrs) to define a variable under variable list
    variables = [setvar("env", "dev")]

    deployments = [MySQLDeployment, PHPDeployment]


class TwoBlueprint(Blueprint):
    """sample bp description"""

    credentials = [basic_cred(CRED_USERNAME, CRED_PASSWORD, default=True)]
    services = [MySQLService, PHPService]
    packages = [MySQLPackage, PHPPackage]
    substrates = [AHVMedVM, AHVMedVMForPHP]
    profiles = [NxProfile]


def test_json():
    """Test the generated json for a single VM
    against known output"""
    import os

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "two_vm_bp_output.json")

    generated_json = TwoBlueprint.json_dumps(pprint=True)
    known_json = open(file_path).read()

    assert generated_json == known_json


def test_yaml():
    """Test the generated yaml for a single VM
    against known output"""
    import os
    from io import StringIO

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "two_vm_bp_output.yaml")

    out = StringIO()
    TwoBlueprint.yaml_dump(stream=out)
    generated_yaml = out.getvalue()
    known_yaml = open(file_path).read()

    assert generated_yaml == known_yaml


# TODO - FIX roundtrip, look at __kind__ attr
"""
def test_json_loads():

    json_data = TwoBlueprint.json_dumps(pprint=True)
    print(json_data)

    B = TwoBlueprint.json_loads(json_data)
    new_json_data = B.json_dumps(pprint=True)
    print(new_json_data)

    assert new_json_data == json_data
"""


def main():
    print(TwoBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    test_json()
    test_yaml()
    # main()
