"""
Single Vm deployment interface for Calm DSL

Limitations:
Only 1 Service & 1 Package allowed per Deployment
Only 1 Profile per Blueprint

"""
import sys
import json

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import SingleVmDeployment, SingleVmBlueprint
from calm.dsl.builtins import read_provider_spec, read_spec, read_local_file
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import action, parallel

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server")
# Setting the recursion limit to max for
sys.setrecursionlimit(100000)


class MySQLDeployment(SingleVmDeployment):
    """MySQL deployment description"""

    # VM Spec
    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")

    # All service, package and substrate system actions
    @action
    def __install__():
        Task.Exec.ssh(name="Task1", filename="scripts/mysql_install_script.sh")

    @action
    def __start__():
        Task.Exec.ssh(name="Task2", script="echo 'Service start in ENV=@@{ENV}@@'")

    @action
    def __stop__():
        Task.Exec.ssh(name="Task3", script="echo 'Service stop in ENV=@@{ENV}@@'")

    @action
    def __pre_create__():
        Task.Exec.escript(name="Pre Create Task", script="print 'Hello!'")


class SampleSingleVmBluerint(SingleVmBlueprint):
    """Simple blueprint Spec"""

    nameserver = Var(DNS_SERVER, label="Local DNS resolver")

    credentials = [
        basic_cred(CRED_USERNAME, CRED_PASSWORD, name="default cred", default=True)
    ]
    deployments = [MySQLDeployment]

    @action  # Profile level action
    def test_profile_action():

        Task.Exec.ssh(name="Task9", script='echo "Hello"', target=ref(MySQLDeployment))


if __name__ == "__main__":
    print(
        json.dumps(
            SampleSingleVmBluerint.make_bp_dict(), indent=4, separators=(",", ": ")
        )
    )
