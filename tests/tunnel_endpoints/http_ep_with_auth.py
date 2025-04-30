"""
Calm HTTP Endpoint Sample with Auth
"""
import json
from calm.dsl.builtins.models.metadata import Metadata
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.builtins.models.calm_ref import Ref
from tests.utils import (
    get_vpc_tunnel_using_account,
    get_vpc_project,
    replace_host_port_in_tests_url,
)

AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
URL = read_local_file(".tests/runbook_tests/url")
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

VPC_TUNNEL_OBJ = get_vpc_tunnel_using_account(DSL_CONFIG)
VPC_PROJECT = get_vpc_project(DSL_CONFIG)

URL = replace_host_port_in_tests_url(URL)

DslHTTPEndpoint = Endpoint.HTTP(
    URL,
    verify=True,
    auth=Endpoint.Auth(AUTH_USERNAME, AUTH_PASSWORD),
    tunnel=Ref.Tunnel(name=VPC_TUNNEL_OBJ["name"]),
)


class EndpointMetadata(Metadata):
    project = Ref.Project(VPC_PROJECT["name"])
