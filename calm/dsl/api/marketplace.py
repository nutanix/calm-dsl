from .resource import ResourceAPI
from .connection import REQUEST

class MarketPlaceAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="calm_marketplace_items")
    
