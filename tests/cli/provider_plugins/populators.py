from calm.dsl.api.handle import get_api_client
from calm.dsl.log.logger import get_logging_handle
from calm.dsl.providers.plugins.aws_vm.constants import AWS as AWS_CONSTANTS
from calm.dsl.providers.plugins.aws_vm.main import AwsVmProvider
from tests.cli.provider_plugins import constants as CONSTANTS
from calm.dsl.providers.plugins.azure_vm.main import Azure

_RESOURCE_POPULATOR_OBJECT = None

LOG = get_logging_handle(__name__)


class ResourcePopulator:
    """Helpers to populate cache with provider related resource info"""

    def __init__(self) -> None:
        self.aws_resource_info = {}
        self.gcp_resource_info = {}
        self.vmw_resource_info = {}
        self.ahv_resource_info = {}
        self.azure_resource_info = {}

    def populate_provider_resource_info(self, provider_type):
        """This method will collect resource info for particular provider"""
        provider_methods = {
            "AWS_VM": self.__populate_aws_resources,
            "AHV_VM": self.__populate_ahv_resources,
            "VMWARE_VM": self.__populate_vmw_resources,
            "GCP_VM": self.__populate_gcp_resources,
            "AZURE_VM": self.__populate_azure_resources,
        }
        return (provider_methods[provider_type])()

    def get_resource_info(self, provider_type):
        provider_resource_info = {
            "AWS_VM": self.aws_resource_info,
            "AHV_VM": self.ahv_resource_info,
            "VMWARE_VM": self.vmw_resource_info,
            "GCP_VM": self.gcp_resource_info,
            "AZURE_VM": self.azure_resource_info,
        }
        return provider_resource_info[provider_type]

    def __populate_aws_resources(self):
        """Get aws resource info and store them"""
        LOG.info("Collecting aws resource info")

        client = get_api_client()
        Obj = AwsVmProvider.get_api_obj()

        # get projects
        projects = client.project.get_name_uuid_map()
        projects_list = list(projects.keys())

        self.aws_resource_info["projects"] = {}
        for project in CONSTANTS.AWS.PROJECTS:
            if project in projects_list:
                self.aws_resource_info["projects"][project] = projects_list.index(
                    project
                )

        # get accounts
        self.aws_resource_info["accounts"] = {}

        payload = {"filter": "type==aws"}
        res, err = client.account.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()

        for entity in res["entities"]:
            entity_name = entity["metadata"]["name"]
            entity_id = entity["metadata"]["uuid"]
            if entity_name.startswith("aws_cloud"):
                self.aws_resource_info["accounts"]["primary_account"] = {
                    "uuid": entity_id
                }
            elif entity_name.startswith("aws_second_cloud"):
                self.aws_resource_info["accounts"]["secondary_account"] = {
                    "uuid": entity_id
                }

        # get instance_types
        instance_types = Obj.machine_types()
        self.aws_resource_info["instance_types"] = {}
        for type in CONSTANTS.AWS.INSTANCE_TYPES:
            if type in instance_types:
                self.aws_resource_info["instance_types"][type] = instance_types.index(
                    type
                )

        # get volume_types
        volume_types_names = list(AWS_CONSTANTS.VOLUME_TYPE_MAP.keys())
        self.aws_resource_info["volume_types"] = {}
        for type in CONSTANTS.AWS.VOLUME_TYPES:
            if type in volume_types_names:
                self.aws_resource_info["volume_types"][type] = volume_types_names.index(
                    type
                )

        # get accounts related info
        for account in self.aws_resource_info["accounts"].keys():
            account_uuid = self.aws_resource_info["accounts"][account]["uuid"]
            # get regions related info
            regions = Obj.regions(account_uuid)
            self.aws_resource_info["accounts"][account]["regions"] = {}
            for region in CONSTANTS.AWS.REGIONS:
                region_related_info = {}
                if region in regions:
                    region_related_info = {"index": regions.index(region)}

                    # get availibility zones
                    avail_zones = Obj.availability_zones(account_uuid, region)
                    region_related_info["availability_zones"] = {}
                    for avail_zone in CONSTANTS.AWS.AVAILABILITY_ZONES:
                        if avail_zone in avail_zones:
                            region_related_info["availability_zones"][
                                avail_zone
                            ] = avail_zones.index(avail_zone)

                    # get machine image
                    machine_images = Obj.mixed_images(account_uuid, region)
                    machine_images_list = list(machine_images.keys())
                    machine_images_list.sort(key=lambda y: y.lower())
                    region_related_info["machine_images"] = {}
                    for image in CONSTANTS.AWS.MACHINE_IMAGES:
                        if image in machine_images_list:
                            region_related_info["machine_images"][
                                image
                            ] = machine_images_list.index(image)

                    # get IAM roles
                    iam_roles = Obj.roles(account_uuid, region)
                    region_related_info["iam_roles"] = {}
                    for role in CONSTANTS.AWS.IAM_ROLES:
                        if role in iam_roles:
                            region_related_info["iam_roles"][role] = iam_roles.index(
                                role
                            )

                    # get key pairs
                    key_pairs = Obj.key_pairs(account_uuid, region)
                    region_related_info["key_pairs"] = {}
                    for key_pair in CONSTANTS.AWS.KEY_PAIRS:
                        if key_pair in key_pairs:
                            region_related_info["key_pairs"][
                                key_pair
                            ] = key_pairs.index(key_pair)

                    # get VPCs
                    vpcs = Obj.VPCs(account_uuid, region)
                    vpc_ids = list(vpcs.values())
                    region_related_info["vpcs"] = {}
                    for vpcid in CONSTANTS.AWS.VPC_IDS:
                        if vpcid in vpc_ids:
                            region_related_info["vpcs"][vpcid] = {
                                "index": vpc_ids.index(vpcid)
                            }

                            sg_name_id_map = Obj.security_groups(
                                account_uuid, region, vpcid
                            )
                            sg_id_list = list(sg_name_id_map.values())
                            security_groups = {}
                            for sg in CONSTANTS.AWS.SECURITY_GROUPS:
                                if sg in sg_id_list:
                                    security_groups[sg] = sg_id_list.index(sg)

                            region_related_info["vpcs"][vpcid][
                                "security_groups"
                            ] = security_groups

                    # get subnets
                    region_related_info["subnets"] = {}
                    for vpcid in region_related_info["vpcs"].keys():
                        for avail_zone in region_related_info[
                            "availability_zones"
                        ].keys():
                            subnets = Obj.subnets(
                                account_uuid, region, vpcid, avail_zone
                            )
                            for subnet in CONSTANTS.AWS.SUBNETS:
                                if subnet in subnets:
                                    region_related_info["subnets"] = {
                                        vpcid: {
                                            avail_zone: {subnet: subnets.index(subnet)}
                                        }
                                    }

                    self.aws_resource_info["accounts"][account]["regions"][
                        region
                    ] = region_related_info

    def __populate_vmw_resources(self):
        """Get vmw resource info and store them"""
        pass

    def __populate_gcp_resources(self):
        """Get gcp resource info and store them"""
        pass

    def __populate_ahv_resources(self):
        """Get ahv resource info and store them"""
        pass

    def __populate_azure_resources(self):
        client = get_api_client()
        Obj = Azure(client.connection)

        # get projects
        projects = client.project.get_name_uuid_map()
        project_list = list(projects.keys())

        self.azure_resource_info["projects"] = {}
        for project in CONSTANTS.AZURE.PROJECTS:
            if project in project_list:
                self.azure_resource_info["projects"][project] = project_list.index(
                    project
                )

        # get accounts
        payload = {"filter": "type==azure"}
        res, err = client.account.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()

        reg_accounts = []
        for entity in res["entities"]:
            entity_name = entity["metadata"]["name"]
            entity_id = entity["metadata"]["uuid"]
            if entity_name.startswith("azure_primary_cloud"):
                reg_accounts.append(entity_id)
            elif entity_name.startswith("azure_secondary_cloud"):
                reg_accounts.append(entity_id)

        index = 1
        # adding accounts
        self.azure_resource_info["accounts"] = {}
        for entity in res["entities"]:
            account_details = {}
            entity_name = entity["metadata"]["name"]
            entity_id = entity["metadata"]["uuid"]
            if entity_id in reg_accounts:
                entity_name = entity_name.split("_")
                entity_name = entity_name[0] + "_" + entity_name[1]
                account_details[entity_name] = {}
                account_details[entity_name]["uuid"] = entity_id
                account_details[entity_name]["index"] = index
                index += 1

                # adding resource groups
                res_groups_in_acnt = Obj.resource_groups(entity_id)
                account_details[entity_name]["resource_groups"] = {}
                for resource_group in CONSTANTS.AZURE.RESOURCE_GROUPS:
                    if resource_group in res_groups_in_acnt:
                        resource_group_dict = {resource_group: {}}
                        resource_group_dict[resource_group][
                            "index"
                        ] = res_groups_in_acnt.index(resource_group)

                        # adding availability sets
                        resource_group_dict[resource_group]["availability_sets"] = {}
                        availability_sets = Obj.availability_sets(
                            entity_id, resource_group
                        )
                        availability_sets = list(availability_sets.keys())
                        for availability_set in CONSTANTS.AZURE.AVAILABILITY_SETS:
                            if availability_set in availability_sets:
                                avlbty_set_details = {availability_set: {}}
                                avlbty_set_details[availability_set][
                                    "index"
                                ] = availability_sets.index(availability_set)
                                resource_group_dict[resource_group][
                                    "availability_sets"
                                ].update(avlbty_set_details)
                        account_details[entity_name]["resource_groups"].update(
                            resource_group_dict
                        )

                        # adding Locations
                        account_details[entity_name]["locations"] = {}
                        locations = Obj.locations(entity_id)
                        location_names = list(locations.keys())
                        for location in CONSTANTS.AZURE.LOCATIONS:
                            if location in location_names:
                                location_details = {location: {}}
                                location_details[location][
                                    "index"
                                ] = location_names.index(location)

                                # adding hardware profile
                                location_details[location]["hw_profiles"] = {}
                                location_id = locations[location]
                                hardware_profiles = Obj.hardware_profiles(
                                    entity_id, location_id
                                )
                                hw_profile_names = list(hardware_profiles.keys())
                                for hardware_profile in CONSTANTS.AZURE.HW_PROFILES:
                                    if hardware_profile in hw_profile_names:
                                        hw_profile_dict = {hardware_profile: {}}
                                        hw_profile_dict[hardware_profile][
                                            "index"
                                        ] = hw_profile_names.index(hardware_profile)
                                        location_details[location][
                                            "hw_profiles"
                                        ].update(hw_profile_dict)

                                # adding publishers
                                location_details[location]["publishers"] = {}
                                publishers = Obj.image_publishers(
                                    entity_id, location_id
                                )
                                for publisher in CONSTANTS.AZURE.PUBLISHERS:
                                    publisher_details = {}
                                    if publisher in publishers:
                                        publisher_details[publisher] = {}
                                        publisher_details[publisher][
                                            "index"
                                        ] = publishers.index(publisher)

                                        # adding image offers
                                        publisher_details[publisher][
                                            "image_offers"
                                        ] = {}
                                        image_offers = Obj.image_offers(
                                            entity_id, location_id, publisher
                                        )
                                        for image_offer in CONSTANTS.AZURE.IMAGE_OFFERS:
                                            image_details = {}
                                            if image_offer in image_offers:
                                                image_details[image_offer] = {}
                                                image_details[image_offer][
                                                    "index"
                                                ] = image_offers.index(image_offer)

                                                # adding SKU's
                                                image_details[image_offer][
                                                    "image_skus"
                                                ] = {}
                                                image_skus = Obj.image_skus(
                                                    entity_id,
                                                    location_id,
                                                    publisher,
                                                    image_offer,
                                                )
                                                for (
                                                    image_sku
                                                ) in CONSTANTS.AZURE.IMAGE_SKUS:
                                                    image_sku_details = {}
                                                    if image_sku in image_skus:
                                                        image_sku_details[
                                                            image_sku
                                                        ] = {}
                                                        image_sku_details[image_sku][
                                                            "index"
                                                        ] = image_skus.index(image_sku)

                                                        # adding image versions
                                                        image_sku_details[image_sku][
                                                            "image_versions"
                                                        ] = {}
                                                        image_versions = (
                                                            Obj.image_versions(
                                                                entity_id,
                                                                location_id,
                                                                publisher,
                                                                image_offer,
                                                                image_sku,
                                                            )
                                                        )
                                                        for (
                                                            image_version
                                                        ) in (
                                                            CONSTANTS.AZURE.IMAGE_VERSIONS
                                                        ):
                                                            if (
                                                                image_version
                                                                in image_versions
                                                            ):
                                                                image_version_dict = {}
                                                                image_version_dict[
                                                                    image_version
                                                                ] = {}
                                                                image_version_dict[
                                                                    image_version
                                                                ][
                                                                    "index"
                                                                ] = image_versions.index(
                                                                    image_version
                                                                )
                                                                image_sku_details[
                                                                    image_sku
                                                                ][
                                                                    "image_versions"
                                                                ].update(
                                                                    image_version_dict
                                                                )
                                                        image_details[image_offer][
                                                            "image_skus"
                                                        ].update(image_sku_details)

                                                publisher_details[publisher][
                                                    "image_offers"
                                                ].update(image_details)
                                        location_details[location]["publishers"].update(
                                            publisher_details
                                        )

                                # adding custom images
                                location_details[location]["custom images"] = {}
                                custom_images = Obj.custom_images(
                                    entity_id, location_id
                                )
                                custom_images = list(custom_images.keys())
                                for custom_image in CONSTANTS.AZURE.CUSTOM_IMAGES:
                                    if custom_image in custom_images:
                                        custom_image_details = {custom_image: {}}
                                        custom_image_details[custom_image][
                                            "index"
                                        ] = custom_images.index(custom_image)
                                        location_details[location][
                                            "custom images"
                                        ].update(custom_image_details)

                                # adding security group
                                security_groups = Obj.security_groups(
                                    entity_id, resource_group, location_id
                                )
                                location_details[location]["security_groups"] = {}
                                for security_group in CONSTANTS.AZURE.SECURITY_GROUPS:
                                    security_group_dict = {}
                                    if security_group in security_groups:
                                        security_group_dict[security_group] = {}
                                        security_group_dict[security_group][
                                            "index"
                                        ] = security_groups.index(security_group)
                                        location_details[location][
                                            "security_groups"
                                        ].update(security_group_dict)

                                # adding virtual networks
                                virtual_networks = Obj.virtual_networks(
                                    entity_id, resource_group, location_id
                                )
                                location_details[location]["virtual_networks"] = {}
                                for virtual_network in CONSTANTS.AZURE.VIRTUAL_NETWORKS:
                                    virtual_network_dict = {}
                                    if virtual_network in virtual_networks:
                                        virtual_network_dict[virtual_network] = {}
                                        virtual_network_dict[virtual_network][
                                            "index"
                                        ] = virtual_networks.index(virtual_network)

                                        # adding subnets
                                        virtual_network_dict[virtual_network][
                                            "subnets"
                                        ] = {}
                                        subnets = Obj.subnets(
                                            entity_id, resource_group, virtual_network
                                        )
                                        for subnet in CONSTANTS.AZURE.SUBNETS:
                                            if subnet in subnets:
                                                subnet_dict = {subnet: {}}
                                                subnet_dict[subnet][
                                                    "index"
                                                ] = subnets.index(subnet)
                                                virtual_network_dict[virtual_network][
                                                    "subnets"
                                                ].update(subnet_dict)
                                        location_details[location][
                                            "virtual_networks"
                                        ].update(virtual_network_dict)
                                account_details[entity_name]["locations"].update(
                                    location_details
                                )
                        self.azure_resource_info["accounts"].update(account_details)


def get_resource_populator_object():
    global _RESOURCE_POPULATOR_OBJECT

    if not _RESOURCE_POPULATOR_OBJECT:
        _RESOURCE_POPULATOR_OBJECT = ResourcePopulator()

    return _RESOURCE_POPULATOR_OBJECT
