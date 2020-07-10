"""
Calm HTTP Endpoint Sample with Auth
"""
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import CalmEndpoint as Endpoint

AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
URL = read_local_file(".tests/runbook_tests/url")

DslHTTPEndpoint = Endpoint.HTTP(
    URL, verify=True, auth=Endpoint.Auth(AUTH_USERNAME, AUTH_PASSWORD)
)


def main():
    print(DslHTTPEndpoint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
