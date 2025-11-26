from .resource import ResourceAPI
from .connection import REQUEST


class TunnelAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="tunnels")
        self.TUNNEL_ENTITY_USAGE = "{}/{}".format(self.PREFIX, "{}/entity_references")

    def entity_references(self, uuid, ignore_error=False):
        """
        GET tunnel entity references
        """
        endpoint = self.TUNNEL_ENTITY_USAGE.format(uuid)
        return self.connection._call(
            endpoint=endpoint,
            method=REQUEST.METHOD.GET,
            verify=False,
            ignore_error=ignore_error,
        )
