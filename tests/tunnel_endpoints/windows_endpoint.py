"""
Calm Endpoint Sample of type Windows
"""
import json
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import basic_cred
from calm.dsl.builtins.models.metadata import Metadata
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.builtins.models.calm_ref import Ref
from tests.utils import get_vpc_project

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/windows_vm_ip")
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

VPC_PROJECT = get_vpc_project(DSL_CONFIG)
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="endpoint_cred")
DslWindowsEndpoint = Endpoint.Windows.ip(
    [VM_IP], connection_protocol="HTTPS", cred=WindowsCred
)


class EndpointMetadata(Metadata):
    project = Ref.Project(VPC_PROJECT["name"])
