from .resource import ResourceAPI
from .connection import REQUEST


class MarketPlaceAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="calm_marketplace_items")
        self.VARIABLE_VALUES = self.ITEM + "/variables/{}/values"

    # https://jira.nutanix.com/browse/CALM-33232
    # Marketplace API taking more than 30s so setting it to 300s
    def variable_values(self, uuid, var_uuid, payload={}):
        url = self.VARIABLE_VALUES.format(uuid, var_uuid)
        return self.connection._call(
            url,
            verify=False,
            method=REQUEST.METHOD.POST,
            request_json=payload,
            timeout=(5, 300),
        )
