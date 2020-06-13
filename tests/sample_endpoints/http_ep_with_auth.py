"""
Calm HTTP Endpoint Sample with Auth
"""
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import CalmEndpoint, Auth

AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
URL = read_local_file(".tests/runbook_tests/url")

DslHTTPEndpoint = CalmEndpoint.HTTP(
    URL, verify=True, auth=Auth.Basic(AUTH_USERNAME, AUTH_PASSWORD)
)


def main():
    print(DslHTTPEndpoint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
