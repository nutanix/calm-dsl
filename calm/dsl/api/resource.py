from .connection import REQUEST


class ResourceAPI:

    ROOT = "api/nutanix/v3"
    CALM_ROOT = "api/calm/v3.0"

    def __init__(self, connection, resource_type, calm_api=False):
        self.connection = connection
        self.PREFIX = (self.CALM_ROOT if calm_api else self.ROOT) + "/" + resource_type
        self.LIST = self.PREFIX + "/list"
        self.ITEM = self.PREFIX + "/{}"

    def create(self, payload):
        return self.connection._call(
            self.PREFIX, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def read(self, id=None):
        url = self.ITEM.format(id) if id else self.PREFIX
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def update(self, uuid, payload):
        return self.connection._call(
            self.ITEM.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    def delete(self, uuid):
        return self.connection._call(
            self.ITEM.format(uuid), verify=False, method=REQUEST.METHOD.DELETE
        )

    def list(self, params={}, ignore_error=False):
        return self.connection._call(
            self.LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
        )

    def get_name_uuid_map(self, params={}):
        response, err = self.list(params)

        if not err:
            response = response.json()
        else:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        total_matches = response["metadata"]["total_matches"]
        if total_matches == 0:
            return {}

        name_uuid_map = {}

        for entity in response["entities"]:
            entity_name = entity["status"]["name"]
            entity_uuid = entity["metadata"]["uuid"]

            if entity_name in name_uuid_map:
                uuid = name_uuid_map[entity_name]

                if type(uuid) is str:
                    uuids = uuid.split()
                    uuids.append(entity_uuid)
                    name_uuid_map[entity_name] = uuids

                elif type(uuid) is list:
                    uuid.append(entity_uuid)
                    name_uuid_map[entity_name] = uuid

            else:
                name_uuid_map[entity_name] = entity_uuid

        return name_uuid_map

    def get_uuid_name_map(self, params={}):
        response, err = self.list(params)
        if not err:
            response = response.json()
        else:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        total_matches = response["metadata"]["total_matches"]
        if total_matches == 0:
            return {}

        uuid_name_map = {}
        for entity in response["entities"]:
            entity_name = entity["status"]["name"]
            entity_uuid = entity["metadata"]["uuid"]

            uuid_name_map[entity_uuid] = entity_name

        return uuid_name_map

    def list_all(self, api_limit=250):
        """returns the list of entities"""

        final_list = []
        offset = 0
        while True:
            response, err = self.list(
                params={
                    "length": api_limit,
                    "offset": offset,
                    "sort_attribute": "_created_timestamp_usecs_",
                    "sort_order": "ASCENDING",
                }
            )
            if not err:
                response = response.json()
            else:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            final_list.extend(response["entities"])

            total_matches = response["metadata"]["total_matches"]
            if total_matches <= (api_limit + offset):
                break

            offset += api_limit

        return final_list


def get_resource_api(resource_type, connection, calm_api=False):
    return ResourceAPI(connection, resource_type, calm_api=calm_api)
