"""
Generated project DSL (.py)
Decompiles project's  providers, users and quotas if available.
"""
import json

from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref
from calm.dsl.runbooks import read_local_file

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TUNNEL_1 = DSL_CONFIG["TUNNELS"]["TUNNEL_1"]["NAME"]
TUNNEL_2 = DSL_CONFIG["TUNNELS"]["TUNNEL_2"]["NAME"]

ACCOUNT_NAME = "NTNX_LOCAL_AZ"

class General_Project(Project):

    providers = [
        Provider.Ntnx(
            account=Ref.Account(ACCOUNT_NAME),
        ),
    ]

    tunnel_references = [
        Ref.Tunnel.Account(name=TUNNEL_1),
        Ref.Tunnel.Account(name=TUNNEL_2),
    ]
