"""
Calm Windows Endpoint Sample
"""
import json

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import CalmEndpoint as Endpoint, basic_cred
from calm.dsl.builtins import Ref

CRED_USERNAME = 'dummy_username'
CRED_PASSWORD = 'dummy_password'
VM_IP = '11.11.11.11'

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TUNNEL_1 = DSL_CONFIG["TUNNELS"]["TUNNEL_1"]["NAME"]

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")

DslLinuxEndpoint = Endpoint.Windows.ip(
    [VM_IP],
    cred=Cred,
    tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
    connection_protocol="HTTPS",
    port=5986
)
