from calm.dsl.runbooks import read_local_file, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint


linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="linux_cred")

LinuxEndpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)
