from .resource import ResourceAPI
from .connection import REQUEST


class ApprovalAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="approvals", calm_api=True)

    def update_approval(
        self, uuid, set_uuid, element_uuid, state, spec_version, comment=None
    ):
        ITEM = self.PREFIX + "/{}/approval_sets/{}/approval_elements/{}"
        payload = {
            "state": state,
            "comment": comment or "",
            "spec_version": spec_version,
        }
        url = ITEM.format(uuid, set_uuid, element_uuid)
        return self.connection._call(
            url,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )
