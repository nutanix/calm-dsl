import json

from calm.dsl.runbooks import read_local_file, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))


linux_ip = DSL_CONFIG["EXISTING_MACHINE"]["IP_2"]
CRED_USERNAME = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["LINUX"]["USERNAME"]
CRED_PASSWORD = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["LINUX"]["PASSWORD"]

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="linux_cred")

LinuxEndpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)
