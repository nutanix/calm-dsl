from calm.dsl.api.handle import get_api_client
from calm.dsl.log.logger import get_logging_handle
from calm.dsl.providers.plugins.aws_vm.constants import AWS as AWS_CONSTANTS
from calm.dsl.providers.plugins.aws_vm.main import AwsVmProvider
import tests.cli.provider_plugins.constants as CONSTANTS

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
            "VMW_VM": self.__populate_vmw_resources,
            "GCP_VM": self.__populate_gcp_resources,
            "AZURE_VM": self.__populate_azure_resources,
        }
        return (provider_methods[provider_type])()

    def get_resource_info(self, provider_type):
        provider_resource_info = {
            "AWS_VM": self.aws_resource_info,
            "AHV_VM": self.ahv_resource_info,
            "VMW_VM": self.vmw_resource_info,
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
        """Get azure resource info and store them"""


def get_resource_populator_object():

    global _RESOURCE_POPULATOR_OBJECT

    if not _RESOURCE_POPULATOR_OBJECT:
        _RESOURCE_POPULATOR_OBJECT = ResourcePopulator()

    return _RESOURCE_POPULATOR_OBJECT
