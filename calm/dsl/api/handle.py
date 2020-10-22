from calm.dsl.config import get_context

from .connection import (
    get_connection_obj,
    get_connection_handle,
    update_connection_handle,
    REQUEST,
)
from .blueprint import BlueprintAPI
from .endpoint import EndpointAPI
from .runbook import RunbookAPI
from .application import ApplicationAPI
from .project import ProjectAPI
from .setting import SettingAPI
from .marketplace import MarketPlaceAPI
from .app_icons import AppIconAPI
from .version import VersionAPI
from .showback import ShowbackAPI
from .user import UserAPI
from .user_group import UserGroupAPI
from .role import RoleAPI
from .directory_service import DirectoryServiceAPI
from .access_control_policy import AccessControlPolicyAPI
from .environment import EnvironmentAPI


class ClientHandle:
    def __init__(self, connection):
        self.connection = connection

    def _connect(self):

        self.connection.connect()

        # Note - add entity api classes here
        self.project = ProjectAPI(self.connection)
        self.blueprint = BlueprintAPI(self.connection)
        self.endpoint = EndpointAPI(self.connection)
        self.runbook = RunbookAPI(self.connection)
        self.application = ApplicationAPI(self.connection)
        self.account = SettingAPI(self.connection)
        self.market_place = MarketPlaceAPI(self.connection)
        self.app_icon = AppIconAPI(self.connection)
        self.version = VersionAPI(self.connection)
        self.showback = ShowbackAPI(self.connection)
        self.user = UserAPI(self.connection)
        self.group = UserGroupAPI(self.connection)
        self.role = RoleAPI(self.connection)
        self.directory_service = DirectoryServiceAPI(self.connection)
        self.acp = AccessControlPolicyAPI(self.connection)
        self.environment = EnvironmentAPI(self.connection)


def get_client_handle_obj(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """returns object of ClientHandle class"""

    connection = get_connection_obj(host, port, auth_type, scheme, auth)
    handle = ClientHandle(connection)
    handle._connect()
    return handle


_API_CLIENT_HANDLE = None


def update_api_client(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """updates global api client object (_API_CLIENT_HANDLE) """

    global _API_CLIENT_HANDLE

    update_connection_handle(host, port, auth_type, scheme=scheme, auth=auth)
    connection = get_connection_handle(host, port, auth_type, scheme, auth)
    _API_CLIENT_HANDLE = ClientHandle(connection)
    _API_CLIENT_HANDLE._connect()

    return _API_CLIENT_HANDLE


def get_api_client():
    """returns global api client object (_API_CLIENT_HANDLE) """

    global _API_CLIENT_HANDLE

    if not _API_CLIENT_HANDLE:
        context = get_context()
        server_config = context.get_server_config()

        pc_ip = server_config.get("pc_ip")
        pc_port = server_config.get("pc_port")
        username = server_config.get("pc_username")
        password = server_config.get("pc_password")

        update_api_client(host=pc_ip, port=pc_port, auth=(username, password))

    return _API_CLIENT_HANDLE
