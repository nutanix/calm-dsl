import json

from calm.dsl.runbooks import read_local_file, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))


linux_ip = ""  # ip address will be filled while executing unit test: tests/unit/run_script/test_run_script_command.py
CRED_USERNAME = "centos"
SSH_KEY = read_local_file(".tests/keys/centos")

LinuxCred = basic_cred(
    CRED_USERNAME,
    SSH_KEY,
    name="linux_cred",
    type="KEY",
    default=True,
)

LinuxEndpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)
