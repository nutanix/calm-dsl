from .resource import ResourceAPI
from .connection import REQUEST


class GlobalVariableApi(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="global_variables", calm_api=True)

        self.USAGE = self.PREFIX + "/{}/usage"
        self.VARIABLE_VALUES = self.PREFIX + "/{}/values"

    def usage(self, id):
        return self.connection._call(
            self.USAGE.format(id), verify=False, method=REQUEST.METHOD.GET
        )

    def values(self, uuid, payload=None):
        url = self.VARIABLE_VALUES.format(uuid)
        return self.connection._call(
            url,
            verify=False,
            method=REQUEST.METHOD.POST,
            request_json=payload,
            ignore_error=True,
        )
