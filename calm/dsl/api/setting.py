from .resource import ResourceAPI
from .connection import REQUEST


class SettingAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="accounts")
        self.VERIFY = self.PREFIX + "/{}/verify"
        self.VMS_LIST = self.ITEM + "/vms/list"

    def verify(self, id):
        return self.connection._call(
            self.VERIFY.format(id), verify=False, method=REQUEST.METHOD.GET
        )

    def vms_list(self, id, params=dict()):
        """returns the vms list for given account"""

        return self.connection._call(
            self.VMS_LIST.format(id),
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
        )

    def get_uuid_type_map(self, params=dict()):
        """returns map containing {account_uuid: account_type} details"""

        res_entities, err = self.list_all(base_params=params, ignore_error=True)
        if err:
            raise Exception(err)

        uuid_type_map = {}
        for entity in res_entities:
            a_uuid = entity["metadata"]["uuid"]
            a_type = entity["status"]["resources"]["type"]
            uuid_type_map[a_uuid] = a_type

        return uuid_type_map
