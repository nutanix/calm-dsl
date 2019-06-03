from .resource import ResourceAPI
from .connection import REQUEST


class SettingAPI(ResourceAPI):

    def __init__(self, connection):
        super().__init__(connection, resource_type="accounts")
        self.VERIFY = self.PREFIX + '/{}/verify'

    def verify(self, id):
        return self.connection._call(
            self.VERIFY.format(id), verify=False, method=REQUEST.METHOD.GET
        )
