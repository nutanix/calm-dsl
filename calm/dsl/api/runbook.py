from .resource import ResourceAPI
from .connection import REQUEST


class RunbookAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="actions")
        #self.UPLOAD = self.PREFIX + "/import_json"
        #self.LAUNCH = self.ITEM + "/simple_launch"
        #self.FULL_LAUNCH = self.ITEM + "/launch"
        #self.LAUNCH_POLL = self.ITEM + "/pending_launches/{}"
