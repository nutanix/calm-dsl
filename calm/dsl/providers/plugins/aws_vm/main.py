import click
import json

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.providers import get_provider_interface
from .constants import AWS as aws


Provider = get_provider_interface()


class AwsVmProvider(Provider):

    provider_type = "AWS_VM"
    package_name = __name__
    spec_template_file = "aws_vm_provider_spec.yaml.jinja2"

    @classmethod
    def create_spec(cls):
        client = get_api_client()
        create_aws_spec(client)


class AWS:
    def __init__(self, connection):
        self.connection = connection

    def regions(self, account_id):
        Obj = get_resource_api("accounts", self.connection)
        res, err = Obj.read(account_id)     # TODO remove it from here
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        region_list = []
        res = res.json()
        entities = res["spec"]["resources"]["data"]["regions"]

        for entity in entities:
            region_list.append(entity["name"])

        return region_list

    def machine_types(self):
        Obj = get_resource_api(aws.MACHINE_TYPES, self.connection)
        res, err = Obj.list()
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_list = []
        res = res.json()
        for entity in res["entities"]:
            entity_list.append(entity["metadata"]["name"])

        return entity_list

    def volume_types(self):
        Obj = get_resource_api(aws.VOLUME_TYPES, self.connection)
        res, err = Obj.list()
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_list = []
        res = res.json()
        for entity in res["entities"]:
            entity_list.append(entity["metadata"]["name"])

        return entity_list

    def availability_zones(self, account_id, region_name):

        payload = {"filter": "account_uuid=={};region=={}". format(account_id, region_name)}
        Obj = get_resource_api(aws.AVAILABILTY_ZONES, self.connection)
        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_list = []
        res = res.json()
        for entity in res["entities"]:
            entity_list.append(entity["metadata"]["name"])

        return entity_list

    def mixed_images(self, account_id, region_name):
        """Returns a map
            m[key] = (tupVal1, tupVal2)
            tupVal1 = id of the image
            tupVal2 = root_device_name of the image
        """

        payload = {"filter": "account_uuid=={};region=={}". format(account_id, region_name)}
        Obj = get_resource_api(aws.MIXED_IMAGES, self.connection)
        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        result = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            image_id = entity["status"]["resources"]["id"]
            root_device_name = entity["status"]["resources"]["root_device_name"]

            result[name] = (image_id, root_device_name)

        return result

    def roles(self, account_id, region_name):

        payload = {"filter": "account_uuid=={};region=={}". format(account_id, region_name)}
        Obj = get_resource_api(aws.ROLES, self.connection)
        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_list = []
        res = res.json()
        for entity in res["entities"]:
            entity_list.append(entity["metadata"]["name"])

        return entity_list

    def key_pairs(self, account_id, region_name):

        payload = {"filter": "account_uuid=={};region=={}". format(account_id, region_name)}
        Obj = get_resource_api(aws.KEY_PAIRS, self.connection)
        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_list = []
        res = res.json()
        for entity in res["entities"]:
            entity_list.append(entity["metadata"]["name"])

        return entity_list

    def VPCs(self, account_id, region_name):

        payload = {"filter": "account_uuid=={};region=={}". format(account_id, region_name)}
        Obj = get_resource_api(aws.VPCS, self.connection)
        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        vpc_cidr_id_map = {}
        for entity in res["entities"]:
            ip_blk = entity["status"]["resources"]["cidr_block"]
            vpc_id = entity["status"]["resources"]["id"]
            vpc_cidr_id_map[ip_blk] = vpc_id

        return vpc_cidr_id_map

    def security_groups(self, account_id, region_name, vpc_id, inc_classic_sg=False):

        inc_classic_sg = "true" if inc_classic_sg else "false"
        payload = {
            "filter": "account_uuid=={};region=={};vpc_id=={};include_classic_sg=={}".
                      format(account_id, region_name, vpc_id, inc_classic_sg)
        }

        Obj = get_resource_api(aws.SECURITY_GROUPS, self.connection)
        res, err = Obj.list(payload)
        res = res.json()

        sg_name_id_map = {}
        for entity in res["entities"]:
            sg_id = entity["status"]["resources"]["id"]
            name = entity["status"]["name"]
            sg_name_id_map[name] = sg_id

        return sg_name_id_map

    def subnets(self, account_id, region_name, vpc_id, availability_zone):

        payload = {
            "filter": "account_uuid=={};region=={};vpc_id=={};availability_zone=={}".
            format(account_id, region_name, vpc_id, availability_zone)
        }

        subnet_list = []
        Obj = get_resource_api(aws.SUBNETS, self.connection)
        res, err = Obj.list(payload)
        res = res.json()

        for entity in res["entities"]:
            subnet_id = entity["status"]["resources"]["id"]
            subnet_list.append(subnet_id)

        return subnet_list


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def create_aws_spec(client):

    spec = {}
    Obj = AWS(client.connection)

    click.echo("")
    spec["name"] = click.prompt("Enter instance name: ", type=str)

    payload = {"filter": "type==aws"}
    res, err = client.account.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    accounts = res.json()
    accounts = accounts["entities"]
    click.echo("Choose from given AWS accounts")
    spec["resources"] = {}

    for ind, account in enumerate(accounts):
        name = account["status"]["name"]
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    if not accounts:
        click.echo("\n{}". format(highlight_text("No AWS account present. Please add first!")))
        return

    while True:
        res = click.prompt("\nEnter the index of account", default=1)
        if res > len(accounts):
            click.echo("Invalid index !!! ")

        else:
            account_name = accounts[res - 1]["status"]["name"]
            account_id = accounts[res - 1]["metadata"]["uuid"]      # TO BE USED

            spec["resources"]["account_uuid"] = account_id
            click.echo("{} selected". format(highlight_text(account_name)))
            break

    choice = click.prompt("\nWant to enable Associate Public Ip Address(y/n)", default="y")
    if choice[0] == "y":
        spec["resources"]["associate_public_ip_address"] = True
    else:
        spec["resources"]["associate_public_ip_address"] = False
        click.echo(highlight_text("Calm and AWS should be in the same private network for scripts to run"))

    click.echo("\nChoose from given instance types")
    ins_types = Obj.machine_types()

    if not ins_types:
        click.echo("\n{}\n". format(highlight_text("No Instance Profiles present")))

    else:
        for ind, name in enumerate(ins_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of instance type", default=1)
            if res > len(ins_types):
                click.echo("Invalid index !!! ")

            else:
                instance_type = ins_types[res - 1]
                spec["resources"]["instance_type"] = instance_type
                click.echo("{} selected". format(highlight_text(instance_type)))
                break

    click.echo("\nChoose from given regions")
    regions = Obj.regions(account_id)

    if not regions:
        click.echo("\n{}\n". format(highlight_text("No regions present")))

    else:
        for ind, name in enumerate(regions):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of region", default=1)
            if res > len(regions):
                click.echo("Invalid index !!! ")

            else:
                region_name = regions[res - 1]      # TO BE USED
                spec["resources"]["region"] = region_name
                click.echo("{} selected". format(highlight_text(region_name)))
                break

    click.echo("\nChoose from given availabilty zones")
    avl_zones = Obj.availability_zones(account_id, region_name)

    if not avl_zones:
        click.echo("\n{}\n". format(highlight_text("No availabilty zones present")))

    else:
        for ind, name in enumerate(avl_zones):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of availability zone", default=1)
            if res > len(avl_zones):
                click.echo("Invalid index !!! ")

            else:
                availability_zone = avl_zones[res - 1]
                spec["resources"]["availability_zone"] = availability_zone
                click.echo("{} selected". format(highlight_text(availability_zone)))
                break

    click.echo("\nChoose from given Machine images")
    mixed_images = Obj.mixed_images(account_id, region_name)
    image_names = list(mixed_images.keys())
    image_names.sort(key=lambda y: y.lower())

    if not image_names:
        click.echo("\n{}\n". format(highlight_text("No machine image present")))

    else:
        for ind, name in enumerate(image_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of machine image", default=1)
            if res > len(image_names):
                click.echo("Invalid index !!! ")

            else:
                image_name = image_names[res - 1]
                res_tuple = mixed_images[image_name]

                image_id = res_tuple[0]
                root_device_name = res_tuple[1]         # TO BE USED
                spec["resources"]["image_id"] = image_id
                click.echo("{} selected". format(highlight_text(image_name)))
                break

    click.echo("\nChoose from given IAM roles")
    ins_pfl_names = Obj.roles(account_id, region_name)

    if not ins_pfl_names:
        click.echo("\n{}\n". format(highlight_text("No instance profile present")))

    else:
        for ind, name in enumerate(ins_pfl_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of IAM role", default=1)
            if res > len(ins_pfl_names):
                click.echo("Invalid index !!! ")

            else:
                role = ins_pfl_names[res - 1]
                spec["resources"]["instance_profile_name"] = role
                click.echo("{} selected". format(highlight_text(role)))
                break

    click.echo("\nChoose from given Key Pairs")
    key_pairs = Obj.key_pairs(account_id, region_name)

    if not key_pairs:
        click.echo("\n{}\n". format(highlight_text("No key pairs present")))

    else:
        for ind, name in enumerate(key_pairs):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of IAM role", default=1)
            if res > len(key_pairs):
                click.echo("Invalid index !!! ")

            else:
                key_name = key_pairs[res - 1]
                spec["resources"]["key_name"] = key_name
                click.echo("{} selected". format(highlight_text(key_name)))
                break

    click.echo("\nChoose from given VPC")
    vpc_map = Obj.VPCs(account_id, region_name)
    cidr_names = list(vpc_map.keys())

    if not cidr_names:
        click.echo("\n{}\n". format(highlight_text("No VPC present")))

    else:
        for ind, name in enumerate(cidr_names):
            dis_name = name + " | " + vpc_map[name]
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(dis_name)))

        while True:
            res = click.prompt("\nEnter the index of VPC", default=1)
            if res > len(cidr_names):
                click.echo("Invalid index !!! ")

            else:
                cidr_name = cidr_names[res - 1]
                vpc_id = vpc_map[cidr_name]     # TO BE USED
                spec["resources"]["vpc_id"] = vpc_id
                dis_name = cidr_name + " | " + vpc_id
                click.echo("{} selected". format(highlight_text(dis_name)))
                break

    choice = click.prompt(highlight_text("\nWant to include security groups(y/n)"), default="n")

    if choice[0] == "y":

        choice = click.prompt(highlight_text("\nInclude Classic Security Groups(y/n)"), default="n")
        if choice[0] == "y":
            sg_map = Obj.security_groups(account_id, region_name, vpc_id, inc_classic_sg=True)
        else:
            sg_map = Obj.security_groups(account_id, region_name, vpc_id)

        spec["resources"]["security_group_list"] = []
        sg_names = list(sg_map.keys())

        while True:
            if not sg_names:
                click.echo("\n{}\n". format(highlight_text("No security group available")))
                break

            else:
                click.echo("\nAvailable security groups: ")
                for ind, name in enumerate(sg_names):
                    dis_name = sg_map[name] + " | " + name
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(dis_name)))

            while True:
                res = click.prompt("\nEnter the index of security group", default=1)
                if res > len(sg_names):
                    click.echo("Invalid index !!! ")

                else:
                    sg_name = sg_names[res - 1]
                    sg_id = sg_map[sg_name]
                    dis_name = sg_id + " | " + sg_name

                    security_group = {
                        "security_group_id": sg_id
                    }

                    spec["resources"]["security_group_list"].append(security_group)
                    click.echo("{} selected". format(highlight_text(dis_name)))
                    sg_names.pop(res - 1)
                    break

            choice = click.prompt(highlight_text("\nWant to add more security_groups(y/n)"), default="n")
            if choice[0] == "n":
                break

    choice = click.prompt(highlight_text("\nWant to include subnets(y/n)"), default="n")

    if choice[0] == "y":

        subnets = Obj.subnets(account_id, region_name, vpc_id, availability_zone)
        click.echo("\nChoose from given subnets")

        if not subnets:
            click.echo("\n{}\n". format(highlight_text("No subnet present")))

        else:
            for ind, name in enumerate(subnets):
                dis_name = name + " | " + vpc_id
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(dis_name)))

            while True:
                res = click.prompt("\nEnter the index of subnet", default=1)
                if res > len(subnets):
                    click.echo("Invalid index !!! ")

                else:
                    subnet_name = subnets[res - 1]
                    spec["resources"]["subnet_id"] = subnet_name
                    dis_name = subnet_name + " | " + vpc_id
                    click.echo("{} selected". format(highlight_text(dis_name)))
                    break

    choice = click.prompt(highlight_text("\nWant to enter user data(y/n)"), default="n")
    if choice[0] == "y":
        user_data = click.prompt("Enter the USER DATA: ", type=str)
        spec["resources"]["user_data"] = user_data

    click.prompt(highlight_text("\nWant to add any tags(y/n)"), default="n")
    if choice[0] == "y":
        tags = []
        while True:
            key = click.prompt("\nKey: ")
            value = click.prompt("Value: ")

            tag = {
                "key": key,
                "value": value
            }
            tags.append(tag)
            choice = click.prompt(highlight_text("\n Want to add more tags(y/n)"), default="n")
            if choice[0] == "n":
                spec["resources"]["tag_list"] = tags
                break

    click.echo("\nEnter the data for root disk")
    click.echo("\nDevice for the root disk: {}". format(highlight_text(root_device_name)))

    spec["resources"]["block_device_map"] = {}
    root_disk = {}
    root_disk["device_name"] = root_device_name
    root_disk["size_gb"] = click.prompt("\nEnter the size of disk(in gb)", default=8)

    volume_types = list(aws.VOLUME_TYPE_MAP.keys())
    click.echo("\nChoose from given volume types: ")
    if not root_device_name:
        click.echo("\n{}\n". format(highlight_text("No device can be added")))

    else:
        for index, name in enumerate(volume_types):
            click.echo("\t{}. {}". format(index + 1, highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index for Volume Type", default=1)
            if res > len(volume_types):
                click.echo("Invalid index !!! ")

            else:
                root_disk["volume_type"] = aws.VOLUME_TYPE_MAP[volume_types[res - 1]]
                click.echo("{} selected". format(highlight_text(volume_types[res - 1])))
                break

        choice = click.prompt("\nWant to delete disk on termination(y/n)", default="y")
        root_disk["delete_on_termination"] = True if choice[0] == "y" else False
        spec["resources"]["block_device_map"]["root_disk"] = root_disk

    choice = click.prompt("\n{}(y/n)". format(highlight_text("Want to add more disks")), default="n")

    avl_device_names = list(aws.DeviceMountPoints.keys())
    spec["resources"]["block_device_map"]["data_disk_list"] = []
    while choice[0] == "y":
        disk = {}
        if not avl_device_names:
            click.echo("\n{}\n". format(highlight_text("No devices present")))
            break

        click.echo("\nChoose from given Device Names: ")
        for index, name in enumerate(avl_device_names):
            click.echo("\t{}. {}". format(index + 1, highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index for Device Name", default=1)
            if res > len(avl_device_names):
                click.echo("Invalid index !!! ")

            else:
                disk["device_name"] = aws.DeviceMountPoints[avl_device_names[res - 1]]
                click.echo("{} selected". format(highlight_text(avl_device_names[res - 1])))
                avl_device_names.pop(res - 1)
                break

        click.echo("\nChoose from given volume types: ")
        for index, name in enumerate(volume_types):
            click.echo("\t{}. {}". format(index + 1, highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index for Volume Type", default=1)
            if res > len(volume_types):
                click.echo("Invalid index !!! ")

            else:
                disk["volume_type"] = aws.VOLUME_TYPE_MAP[volume_types[res - 1]]
                click.echo("{} selected". format(highlight_text(volume_types[res - 1])))
                break

        disk["size_gb"] = click.prompt("\nEnter the size of disk(in gb)", default=8)
        choice = click.prompt("\nWant to delete disk on termination(y/n)", default="y")
        disk["delete_on_termination"] = True if choice[0] == "y" else False

        spec["resources"]["block_device_map"]["data_disk_list"].append(disk)
        choice = click.prompt("\n{}(y/n)". format(highlight_text("Want to add more disks")), default="n")

    AwsVmProvider.validate_spec(spec)
    click.echo("\nCreate spec \n")
    click.echo(highlight_text(json.dumps(spec, sort_keys=True, indent=4)))
