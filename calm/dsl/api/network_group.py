from .resource import ResourceAPI
from .connection import REQUEST


class NetworkGroupAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="network_groups")
        self.CREATE_TUNNEL = self.PREFIX + "/tunnels"
        self.SETUP_TUNNEL = self.PREFIX + "/{}/tunnels"
        self.RESET_TUNNEL = self.PREFIX + "/{}/tunnels"
        self.APP_PENDING_LAUNCH = "api/nutanix/v3/blueprints/{}/pending_launches/{}"
        self.DELETE_NG_TUNNEL = self.PREFIX + "/{}/tunnels/{}"

    def create_network_group_tunnel(self, payload):
        return self.connection._call(
            self.CREATE_TUNNEL,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def setup_network_group_tunnel(self, ng_uuid, payload):
        return self.connection._call(
            self.SETUP_TUNNEL.format(ng_uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def reset_network_group_tunnel_vm(self, ng_uuid, payload):
        # Update tunnel_reference here
        return self.connection._call(
            self.RESET_TUNNEL.format(ng_uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def delete_tunnel(self, ng_uuid, tunnel_uuid):
        return self.connection._call(
            self.DELETE_NG_TUNNEL.format(ng_uuid, tunnel_uuid),
            verify=False,
            method=REQUEST.METHOD.DELETE,
        )

    def read_pending_task(self, uuid, task_uuid):
        return self.connection._call(
            self.APP_PENDING_LAUNCH.format(uuid, task_uuid),
            verify=False,
            method=REQUEST.METHOD.GET,
        )
