from .resource import ResourceAPI
from .connection import REQUEST


class SettingAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="accounts")
        self.VERIFY = self.PREFIX + "/{}/verify"

    def verify(self, id):
        return self.connection._call(
            self.VERIFY.format(id), verify=False, method=REQUEST.METHOD.GET
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
