from .connection import REQUEST


class VersionAPI:
    def __init__(self, connection):
        self.connection = connection

        self.CALM_VERSION = "apps/version"
        self.PC_VERSION = "PrismGateway/services/rest/v1/cluster/version"

    def get_calm_version(self):
        return self.connection._call(
            self.CALM_VERSION, verify=False, method=REQUEST.METHOD.GET,
        )

    def get_pc_version(self):
        return self.connection._call(
            self.PC_VERSION,
            verify=False,
            method=REQUEST.METHOD.GET,
        )
