import json

from calm.dsl.runbooks import read_local_file, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))


windows_ip = DSL_CONFIG["EXISTING_MACHINE"]["WIN_IP_ADDR"]
CRED_USERNAME = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["WINDOWS"]["USERNAME"]
CRED_PASSWORD = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["WINDOWS"]["PASSWORD"]


WindowsCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="windows_cred")

WindowsEndpoint = Endpoint.Windows.ip(
    [windows_ip], connection_protocol="HTTPS", cred=WindowsCred
)
