from .connection import get_connection, REQUEST
from .blueprint import BlueprintAPI
from .application import ApplicationAPI


class ClientHandle:
    def __init__(self, connection):
        self.connection = connection

    def _connect(self):

        self.connection.connect()

        # Note - add entity api classes here
        self.blueprint = BlueprintAPI(self.connection)
        self.application = ApplicationAPI(self.connection)


_CLIENT_HANDLE = None


def get_client_handle(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    global _CLIENT_HANDLE
    if not _CLIENT_HANDLE:
        connection = get_connection(host, port, auth_type, scheme=scheme, auth=auth)
        _CLIENT_HANDLE = ClientHandle(connection)
        _CLIENT_HANDLE._connect()
    return _CLIENT_HANDLE
