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
