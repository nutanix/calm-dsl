from .connection import REQUEST


class ResourceAPI:

    PREFIX = "api/nutanix/v3/"

    def __init__(self, connection):
        self.connection = connection

    def create(self, payload):
        return self.connection._call(
            self.PREFIX,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def read(self, id):
        return self.connection._call(
            self.ITEM.format(id),
            verify=False,
            method=REQUEST.METHOD.GET
        )

    def update(self, uuid, payload):
        return self.connection._call(
            self.ITEM.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    def delete(self, uuid):
        return self.connection._call(
            self.ITEM.format(uuid),
            verify=False,
            method=REQUEST.METHOD.DELETE,
        )

    def list(self, params=None):
        return self.connection._call(
            self.LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
        )

    def get_name_uuid_map(self, params=None):
        response = self.list(params)

        totalMatches = response['metadata']['total_matches']
        if totalMatches == 0:
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
