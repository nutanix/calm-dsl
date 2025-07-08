"""
Calm HTTP Endpoint Sample with Auth
"""
import json

from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.builtins.models.calm_ref import Ref
from calm.dsl.builtins import read_local_file

AUTH_USERNAME = 'dummy_username'
AUTH_PASSWORD = 'dummy_password'
URL = 'dummy_url'
VM_IP = '10.10.10.10'

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TUNNEL_1 = DSL_CONFIG["TUNNELS"]["TUNNEL_1"]["NAME"]

DslHTTPEndpoint = Endpoint.HTTP(
    URL,
    verify=True,
    auth=Endpoint.Auth(AUTH_USERNAME, AUTH_PASSWORD),
    tunnel=Ref.Tunnel.Account(name=TUNNEL_1)
)