from calm.dsl.api.cloud import CloudAPI
from .constants import AHV as ahv


class AHV:

    def __init__(self, connection):
        self.connection = connection

    def images(self):
        Obj = CloudAPI(ahv.IMAGES, self.connection)
        return Obj.get_name_uuid_map()

    def subnets(self):
        Obj = CloudAPI(ahv.SUBNETS, self.connection)
        return Obj.get_name_uuid_map()
