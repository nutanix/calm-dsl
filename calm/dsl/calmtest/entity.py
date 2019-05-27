from ..api.resource import ResourceAPI


class EntityAPI(ResourceAPI):

    def __init__(self, relURL, connection):
        
        super().__init__(connection)
        self.PREFIX = ResourceAPI.PREFIX + relURL
        self.LIST = self.PREFIX + "/list"
        self.ITEM = self.PREFIX + "/{}"
