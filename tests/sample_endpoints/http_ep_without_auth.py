"""
Calm HTTP Endpoint Sample without Auth
"""
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import CalmEndpoint as Endpoint

URL = read_local_file(".tests/runbook_tests/url")
DslHTTPEndpoint = Endpoint.HTTP(
    URL, retries=1, retry_interval=2, timeout=50, verify=True
)


def main():
    print(DslHTTPEndpoint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
