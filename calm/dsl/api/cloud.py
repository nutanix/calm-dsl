from .resource import ResourceAPI


class CloudAPI(ResourceAPI):

    def __init__(self, relURL, connection):

        super().__init__(connection)
        self.PREFIX = ResourceAPI.PREFIX + relURL
        self.LIST = self.PREFIX + "/list"
        self.ITEM = self.PREFIX + "/{}"

    def get_name_uuid_map(self, params=None):
        response, err = self.list(params)

        if not err:
            response = response.json()
        else:
            raise Exception(err)

        total_matches = response['metadata']['total_matches']
        if total_matches == 0:
            return {}

        name_uuid_map = {}

        for entity in response['entities']:
            entity_name = entity['status']['name']
            entity_uuid = entity['metadata']['uuid']

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
