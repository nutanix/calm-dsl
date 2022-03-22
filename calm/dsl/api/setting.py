from .resource import ResourceAPI
from .connection import REQUEST


class AccountsAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="accounts")
        self.VERIFY = self.PREFIX + "/{}/verify"
        self.VMS_LIST = self.ITEM + "/vms/list"
        self.RESOURCE_TYPES_LIST_BASED_ON_ACCOUNT = (
            self.PREFIX + "/{}/resource_types/list"
        )

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

        response, err = self.list(params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        response = response.json()
        total_matches = response["metadata"]["total_matches"]
        if total_matches == 0:
            return {}

        uuid_type_map = {}
        for entity in response["entities"]:
            a_uuid = entity["metadata"]["uuid"]
            a_type = entity["status"]["resources"]["type"]
            uuid_type_map[a_uuid] = a_type

        return uuid_type_map
