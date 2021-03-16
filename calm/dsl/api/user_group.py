from .resource import ResourceAPI


class UserGroupAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="user_groups")

    def get_name_uuid_map(self, params=dict()):

        res, err = self.list(params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()

        name_uuid_map = {}
        for entity in res["entities"]:
            state = entity["status"]["state"]
            if state != "COMPLETE":
                continue

            e_resources = entity["status"]["resources"]

            directory_service_user_group = (
                e_resources.get("directory_service_user_group") or dict()
            )
            distinguished_name = directory_service_user_group.get("distinguished_name")

            directory_service_ref = (
                directory_service_user_group.get("directory_service_reference")
                or dict()
            )
            directory_service_name = directory_service_ref.get("name", "")

            uuid = entity["metadata"]["uuid"]

            if directory_service_name and distinguished_name:
                name_uuid_map[distinguished_name] = uuid

        return name_uuid_map

    def get_uuid_name_map(self, params=dict()):

        res, err = self.list(params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()

        uuid_name_map = {}
        for entity in res["entities"]:
            state = entity["status"]["state"]
            if state != "COMPLETE":
                continue

            e_resources = entity["status"]["resources"]

            directory_service_user_group = (
                e_resources.get("directory_service_user_group") or dict()
            )
            distinguished_name = directory_service_user_group.get("distinguished_name")

            directory_service_ref = (
                directory_service_user_group.get("directory_service_reference")
                or dict()
            )
            directory_service_name = directory_service_ref.get("name", "")

            uuid = entity["metadata"]["uuid"]

            if directory_service_name and distinguished_name:
                uuid_name_map[uuid] = distinguished_name

        return uuid_name_map
