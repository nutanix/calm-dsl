from calm.dsl.config import get_context
from calm.dsl.constants import MULTICONNECT

from .connection import (
    get_connection_obj,
    get_pc_connection_obj,
    get_ncm_connection_obj,
    get_pc_connection_handle,
    get_ncm_connection_handle,
    update_pc_connection_handle,
    update_ncm_connection_handle,
    REQUEST,
    MultiConnection,
)
from .blueprint import BlueprintAPI
from .endpoint import EndpointAPI
from .runbook import RunbookAPI
from .library_tasks import TaskLibraryApi
from .application import ApplicationAPI
from .project import ProjectAPI
from .environment import EnvironmentAPI
from .setting import AccountsAPI
from .marketplace import MarketPlaceAPI
from .app_icons import AppIconAPI
from .version import VersionAPI
from .showback import ShowbackAPI
from .user import UserAPI
from .user_group import UserGroupAPI
from .role import RoleAPI
from .directory_service import DirectoryServiceAPI
from .access_control_policy import AccessControlPolicyAPI
from .app_protection_policy import AppProtectionPolicyAPI
from .job import JobAPI
from .tunnel import TunnelAPI
from .vm_recovery_point import VmRecoveryPointAPI
from .nutanix_task import TaskAPI
from .network_group import NetworkGroupAPI
from .resource_type import ResourceTypeAPI
from .policy_action_type import PolicyActionTypeAPI
from .policy_event import PolicyEventAPI
from .policy_attributes import PolicyAttributesAPI
from .policy import PolicyAPI
from .approval import ApprovalAPI
from .approval_request import ApprovalRequestAPI
from .provider import ProviderAPI
from .quotas import QuotasAPI
from .groups_api import MultiGroupsAPI
from .util import get_auth_info
from .global_variable import GlobalVariableApi


class ClientHandle:
    def __init__(self, connection):
        self.connection = connection

    def _connect(self):
        self.connection.connect()

        # Note - add entity api classes here
        self.project = ProjectAPI(self.connection)
        self.environment = EnvironmentAPI(self.connection)
        self.blueprint = BlueprintAPI(self.connection)
        self.endpoint = EndpointAPI(self.connection)
        self.runbook = RunbookAPI(self.connection)
        self.task = TaskLibraryApi(self.connection)
        self.application = ApplicationAPI(self.connection)
        self.account = AccountsAPI(self.connection)
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
        self.app_protection_policy = AppProtectionPolicyAPI(self.connection)
        self.job = JobAPI(self.connection)
        self.tunnel = TunnelAPI(self.connection)
        self.vm_recovery_point = VmRecoveryPointAPI(self.connection)
        self.nutanix_task = TaskAPI(self.connection)
        self.network_group = NetworkGroupAPI(self.connection)
        self.resource_types = ResourceTypeAPI(self.connection)
        self.policy_action_types = PolicyActionTypeAPI(self.connection)
        self.policy_event = PolicyEventAPI(self.connection)
        self.policy_attributes = PolicyAttributesAPI(self.connection)
        self.policy = PolicyAPI(self.connection)
        self.approvals = ApprovalAPI(self.connection)
        self.approval_requests = ApprovalRequestAPI(self.connection)
        self.provider = ProviderAPI(self.connection)
        self.quotas = QuotasAPI(self.connection)
        self.groups = MultiGroupsAPI(self.connection)
        self.global_variable = GlobalVariableApi(self.connection)


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


def get_multi_client_handle_obj(
    host,
    port,
    ncm_host,
    ncm_port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """returns object of ClientHandle class"""

    multi_connection = MultiConnection()
    setattr(
        multi_connection,
        MULTICONNECT.PC_OBJ,
        get_pc_connection_obj(host, port, auth_type, scheme, auth),
    )
    setattr(
        multi_connection,
        MULTICONNECT.NCM_OBJ,
        get_ncm_connection_obj(ncm_host, ncm_port, auth_type, scheme, auth),
    )

    handle = ClientHandle(multi_connection)
    handle._connect()
    return handle


_API_CLIENT_HANDLE = None


def update_api_client(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
    **kwargs,
):
    """updates global api client object (_API_CLIENT_HANDLE)"""

    global _API_CLIENT_HANDLE

    multi_connection = MultiConnection()

    context = get_context()
    ncm_server_config = context.get_ncm_server_config()
    ncm_enabled = ncm_server_config.get("ncm_enabled", False)
    ncm_host = ncm_server_config.get("host", None)
    ncm_port = ncm_server_config.get("port", None)

    # If ncm is not enabled, use pc host and port for ncm
    # It will create ncm session pointing to PC
    if not ncm_enabled:
        ncm_host = host
        ncm_port = port

    update_pc_connection_handle(host, port, auth_type, scheme=scheme, auth=auth)
    setattr(
        multi_connection,
        MULTICONNECT.PC_OBJ,
        get_pc_connection_handle(host, port, auth_type, scheme, auth),
    )

    update_ncm_connection_handle(
        ncm_host, ncm_port, auth_type, scheme=scheme, auth=auth
    )
    setattr(
        multi_connection,
        MULTICONNECT.NCM_OBJ,
        get_ncm_connection_handle(ncm_host, ncm_port, auth_type, scheme, auth),
    )

    _API_CLIENT_HANDLE = ClientHandle(multi_connection)
    _API_CLIENT_HANDLE._connect()

    return _API_CLIENT_HANDLE


def get_api_client():
    """returns global api client object (_API_CLIENT_HANDLE)"""

    global _API_CLIENT_HANDLE

    if not _API_CLIENT_HANDLE:
        context = get_context()
        server_config = context.get_server_config()

        pc_ip = server_config.get("pc_ip")
        pc_port = server_config.get("pc_port")
        api_key_location = server_config.get("api_key_location", None)
        cred = get_auth_info(api_key_location)
        username = cred.get("username")
        password = cred.get("password")

        update_api_client(host=pc_ip, port=pc_port, auth=(username, password))

    return _API_CLIENT_HANDLE


def reset_api_client_handle():
    """resets global api client object (_API_CLIENT_HANDLE)"""

    global _API_CLIENT_HANDLE
    _API_CLIENT_HANDLE = None
