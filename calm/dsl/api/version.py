from .connection import REQUEST


class VersionAPI:
    def __init__(self, connection):
        self.connection = connection

    def get_calm_version(self):
        return self.connection._call(
            "apps/version", verify=False, method=REQUEST.METHOD.GET,
        )

    def get_pc_version(self):
        return self.connection._call(
            "PrismGateway/services/rest/v1/cluster/version",
            verify=False,
            method=REQUEST.METHOD.GET,
        )
