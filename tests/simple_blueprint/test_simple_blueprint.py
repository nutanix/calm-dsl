"""
Simple deployment interface for Calm DSL

Limitations:
Only 1 Service & 1 Package allowed per Deployment
Only 1 Profile per Blueprint

"""
import sys

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec, read_spec, read_local_file
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import action, parallel

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server")
# Setting the recursion limit to max for
sys.setrecursionlimit(100000)


class MySQLDeployment(SimpleDeployment):
    """MySQL deployment description"""

    ENV = Var.WithOptions.Predefined.string(
        ["DEV", "PROD"], default="DEV", is_mandatory=True, runtime=True
    )

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

    # Custom service actions
    @action
    def custom_action_1():
        blah = Var("2")  # noqa
        Task.Exec.ssh(name="Task4", script='echo "Hello"')
        Task.Exec.ssh(name="Task5", script='echo "Hello again"')

    @action
    def custom_action_2():
        with parallel():  # All tasks within this context will be run in parallel
            Task.Exec.ssh(name="Task41", script="date")
            Task.Exec.ssh(name="Task51", script="date")


class K8SDeployment1(SimpleDeployment):
    """ K8SDeployment Description"""

    deployment_spec = read_spec("specs/deployment1.yaml")
    service_spec = read_spec("specs/service1.yaml")

    # dependencies to indicate provisioning of K8sDeployment1 is dependent of the MySQLDeployment creation
    # deployment-level dependency
    dependencies = [ref(MySQLDeployment)]


class PHPDeployment(SimpleDeployment):
    """PHP deployment description"""

    # Add dependency to MySQL and to K8SDeployment1(deployment-level)
    dependencies = [ref(MySQLDeployment), ref(K8SDeployment1)]

    # Variables
    foo = Var("baz")

    # VM Spec
    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")

    # Deployment level properties
    max_replicas = "2"

    # Service actions
    @action
    def test_action():
        blah = Var("2")  # noqa
        Task.Exec.ssh(name="Task6", script='echo "Hello"')
        Task.Exec.ssh(name="Task7", script='echo "Hello again"')

    @action
    def __install__():
        Task.Exec.ssh(name="Task8", script="echo @@{foo}@@")


class SimpleLampBlueprint(SimpleBlueprint):
    """Simple blueprint Spec"""

    nameserver = Var(DNS_SERVER, label="Local DNS resolver")

    credentials = [
        basic_cred(CRED_USERNAME, CRED_PASSWORD, name="default cred", default=True)
    ]
    deployments = [MySQLDeployment, PHPDeployment, K8SDeployment1]

    @action
    def test_profile_action():

        # Profile level action
        Task.Exec.ssh(name="Task9", script='echo "Hello"', target=ref(MySQLDeployment))

        # Call other actions
        PHPDeployment.test_action(name="Task10")


def test_json():

    import json
    import os

    generated_json = SimpleLampBlueprint.make_bp_dict()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "test_simple_blueprint.json")
    known_json = json.loads(open(file_path).read())

    assert generated_json == known_json
