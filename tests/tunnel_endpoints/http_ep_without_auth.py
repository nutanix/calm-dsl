"""
Calm HTTP Endpoint Sample without Auth
"""
from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import CalmEndpoint as Endpoint

URL = read_local_file(".tests/runbook_tests/url")
DslHTTPEndpoint = Endpoint.HTTP(
    URL,
    retries=1,
    retry_interval=2,
    timeout=50,
    verify=True,
    tunnel=Ref.Tunnel(name="NewNetworkGroupTunnel2"),
)
