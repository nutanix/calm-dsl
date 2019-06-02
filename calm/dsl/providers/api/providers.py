from calm.dsl.api import get_resource_api
from .constants import AHV as ahv


class AHV:

    def __init__(self, connection):
        self.connection = connection

    def images(self):
        Obj = get_resource_api(ahv.IMAGES, self.connection)
        return Obj.get_name_uuid_map()

    def subnets(self):
        Obj = get_resource_api(ahv.SUBNETS, self.connection)
        return Obj.get_name_uuid_map()

    def groups(self):
        Obj = get_resource_api(ahv.GROUPS, self.connection)
        categories = []

        payload = {
            "entity_type": "category",
            "filter_criteria": "name!=CalmApplication;name!=CalmDeployment;name!=CalmService;name!=CalmPackage",
            "grouping_attribute": "abac_category_key",
            "group_sort_attribute": "name",
            "group_count": 60,
            "group_attributes": [
                {
                    "attribute": "name",
                    "ancestor_entity_type": "abac_category_key"
                }
            ],
            "group_member_count": 1000,
            "group_member_offset": 0,
            "group_member_sort_attribute": "value",
            "group_member_attributes": [
                {
                    "attribute": "value"
                }
            ],
            "query_name": "prism:CategoriesQueryModel"
        }

        response, err = Obj.create(payload)
        response = response.json()

        for group in response["group_results"]:

            key = group["group_summaries"]["sum:name"]["values"][0]["values"][0]

            for entity in group["entity_results"]:
                value = entity["data"][0]["values"][0]["values"][0]
                categories.append(
                    {
                        "key": key,
                        "value": value
                    }
                )

        return categories
