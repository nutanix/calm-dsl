import click
from ruamel import yaml
import uuid

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
        create_spec(client)

    @classmethod
    def get_api_obj(cls):
        """returns object to call ahv provider specific apis"""

        client = get_api_client()
        return AWS(client.connection)


class AWS:
    def __init__(self, connection):
        self.connection = connection

    def regions(self, account_id):
        Obj = get_resource_api("accounts", self.connection)
        res, err = Obj.read(account_id)  # TODO remove it from here
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

        payload = {
            "filter": "account_uuid=={};region=={}".format(account_id, region_name)
        }
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

        payload = {
            "filter": "account_uuid=={};region=={}".format(account_id, region_name)
        }
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

        payload = {
            "filter": "account_uuid=={};region=={}".format(account_id, region_name)
        }
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

        payload = {
            "filter": "account_uuid=={};region=={}".format(account_id, region_name)
        }
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

        payload = {
            "filter": "account_uuid=={};region=={}".format(account_id, region_name)
        }
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
            "filter": "account_uuid=={};region=={};vpc_id=={};include_classic_sg=={}".format(
                account_id, region_name, vpc_id, inc_classic_sg
            )
        }

        Obj = get_resource_api(aws.SECURITY_GROUPS, self.connection)
        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()

        sg_name_id_map = {}
        for entity in res["entities"]:
            sg_id = entity["status"]["resources"]["id"]
            name = entity["status"]["name"]
            sg_name_id_map[name] = sg_id

        return sg_name_id_map

    def subnets(self, account_id, region_name, vpc_id, availability_zone):

        payload = {
            "filter": "account_uuid=={};region=={};vpc_id=={};availability_zone=={}".format(
                account_id, region_name, vpc_id, availability_zone
            )
        }

        subnet_list = []
        Obj = get_resource_api(aws.SUBNETS, self.connection)
        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()

        for entity in res["entities"]:
            subnet_id = entity["status"]["resources"]["id"]
            subnet_list.append(subnet_id)

        return subnet_list


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def create_spec(client):

    spec = {}
    Obj = AWS(client.connection)

    vpc_id = None
    region_name = None
    account_id = None
    root_device_name = None

    # VM Configuration

    projects = client.project.get_name_uuid_map()
    project_list = list(projects.keys())

    if not project_list:
        click.echo(highlight_text("No projects found!!!"))
        click.echo(highlight_text("Please add first"))
        return

    click.echo("\nChoose from given projects:")
    for ind, name in enumerate(project_list):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    project_id = ""
    while True:
        ind = click.prompt("\nEnter the index of project", default=1)
        if (ind > len(project_list)) or (ind <= 0):
            click.echo("Invalid index !!! ")

        else:
            project_id = projects[project_list[ind - 1]]
            click.echo("{} selected".format(highlight_text(project_list[ind - 1])))
            break

    res, err = client.project.read(project_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    project = res.json()
    accounts = project["status"]["resources"]["account_reference_list"]

    reg_accounts = []
    for account in accounts:
        reg_accounts.append(account["uuid"])

    payload = {"filter": "type==aws"}
    res, err = client.account.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    aws_accounts = {}

    for entity in res["entities"]:
        entity_name = entity["metadata"]["name"]
        entity_id = entity["metadata"]["uuid"]
        if entity_id in reg_accounts:
            aws_accounts[entity_name] = entity_id

    if not aws_accounts:
        click.echo(
            highlight_text("No aws account found registered in this project !!!")
        )
        click.echo("Please add one !!!")
        return

    accounts = list(aws_accounts.keys())
    spec["resources"] = {}

    click.echo("\nChoose from given AWS accounts")
    for ind, name in enumerate(accounts):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        res = click.prompt("\nEnter the index of account to be used", default=1)
        if (res > len(accounts)) or (res <= 0):
            click.echo("Invalid index !!! ")

        else:
            account_name = accounts[res - 1]
            account_id = aws_accounts[account_name]  # TO BE USED

            spec["resources"]["account_uuid"] = account_id
            click.echo("{} selected".format(highlight_text(account_name)))
            break

    spec["name"] = "vm_{}".format(str(uuid.uuid4())[-10:])
    spec["name"] = click.prompt("\nEnter instance name", default=spec["name"])

    choice = click.prompt("\nEnable Associate Public Ip Address(y/n)", default="y")
    if choice[0] == "y":
        spec["resources"]["associate_public_ip_address"] = True
    else:
        spec["resources"]["associate_public_ip_address"] = False
        click.echo(
            highlight_text(
                "Calm and AWS should be in the same private network for scripts to run"
            )
        )

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add an instance type")), default="n"
    )

    ins_types = Obj.machine_types() if choice[0] == "y" else None

    if (not ins_types) and (choice[0] == "y"):
        click.echo("\n{}".format(highlight_text("No Instance Profile present")))

    elif ins_types:
        click.echo("\nChoose from given instance types")
        for ind, name in enumerate(ins_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of instance type", default=1)
            if (res > len(ins_types)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                instance_type = ins_types[res - 1]
                spec["resources"]["instance_type"] = instance_type
                click.echo("{} selected".format(highlight_text(instance_type)))
                break

    choice = (
        click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add a region")), default="n"
        )
        if account_id
        else "n"
    )

    regions = Obj.regions(account_id) if choice[0] == "y" else None
    if (not regions) and (choice[0] == "y"):
        click.echo("\n{}".format(highlight_text("No region present")))

    elif regions:
        click.echo("\nChoose from given regions")
        for ind, name in enumerate(regions):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of region", default=1)
            if (res > len(regions)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                region_name = regions[res - 1]  # TO BE USED
                spec["resources"]["region"] = region_name
                click.echo("{} selected".format(highlight_text(region_name)))
                break

    choice = (
        click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add a availability zone")),
            default="n",
        )
        if region_name
        else "n"
    )

    avl_zones = (
        Obj.availability_zones(account_id, region_name) if choice[0] == "y" else None
    )
    if (not avl_zones) and (choice[0] == "y"):
        click.echo("\n{}".format(highlight_text("No availabilty zone present")))

    elif avl_zones:
        click.echo("\nChoose from given availabilty zones")
        for ind, name in enumerate(avl_zones):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of availability zone", default=1)
            if (res > len(avl_zones)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                availability_zone = avl_zones[res - 1]
                spec["resources"]["availability_zone"] = availability_zone
                click.echo("{} selected".format(highlight_text(availability_zone)))
                break

    choice = (
        click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add a machine image")),
            default="n",
        )
        if region_name
        else "n"
    )

    mixed_images = Obj.mixed_images(account_id, region_name) if choice[0] == "y" else {}
    image_names = list(mixed_images.keys())
    image_names.sort(key=lambda y: y.lower())
    if (not image_names) and (choice[0] == "y"):
        click.echo("\n{}".format(highlight_text("No machine image present")))

    elif image_names:
        click.echo("\nChoose from given Machine images")
        for ind, name in enumerate(image_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of machine image", default=1)
            if (res > len(image_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                image_name = image_names[res - 1]
                res_tuple = mixed_images[image_name]

                image_id = res_tuple[0]
                root_device_name = res_tuple[1]  # TO BE USED
                spec["resources"]["image_id"] = image_id
                click.echo("{} selected".format(highlight_text(image_name)))
                break

    choice = (
        click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add an IAM Role")), default="n"
        )
        if region_name
        else "n"
    )

    ins_pfl_names = Obj.roles(account_id, region_name) if choice[0] == "y" else None
    if (not ins_pfl_names) and (choice[0] == "y"):
        click.echo("\n{}".format(highlight_text("No instance profile present")))

    elif ins_pfl_names:
        click.echo("\nChoose from given IAM roles")
        for ind, name in enumerate(ins_pfl_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of IAM role", default=1)
            if (res > len(ins_pfl_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                role = ins_pfl_names[res - 1]
                spec["resources"]["instance_profile_name"] = role
                click.echo("{} selected".format(highlight_text(role)))
                break

    choice = (
        click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add any Key Pair")), default="n"
        )
        if region_name
        else "n"
    )

    key_pairs = Obj.key_pairs(account_id, region_name) if choice[0] == "y" else None
    if (not key_pairs) and (choice[0] == "y"):
        click.echo("\n{}".format(highlight_text("No key pair present")))

    elif key_pairs:
        click.echo("\nChoose from given Key Pairs")
        for ind, name in enumerate(key_pairs):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of Key-Pair", default=1)
            if (res > len(key_pairs)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                key_name = key_pairs[res - 1]
                spec["resources"]["key_name"] = key_name
                click.echo("{} selected".format(highlight_text(key_name)))
                break

    choice = (
        click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add any VPC")), default="n"
        )
        if region_name
        else "n"
    )

    vpc_map = Obj.VPCs(account_id, region_name) if choice[0] == "y" else {}
    cidr_names = list(vpc_map.keys())

    if (not cidr_names) and (choice[0] == "y"):
        click.echo("\n{}".format(highlight_text("No VPC present")))

    elif cidr_names:
        click.echo("\nChoose from given VPC")
        for ind, name in enumerate(cidr_names):
            dis_name = name + " | " + vpc_map[name]
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(dis_name)))

        while True:
            res = click.prompt("\nEnter the index of VPC", default=1)
            if (res > len(cidr_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                cidr_name = cidr_names[res - 1]
                vpc_id = vpc_map[cidr_name]  # TO BE USED
                spec["resources"]["vpc_id"] = vpc_id
                dis_name = cidr_name + " | " + vpc_id
                click.echo("{} selected".format(highlight_text(dis_name)))
                break

    choice = (
        click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to include security groups")),
            default="n",
        )
        if vpc_id
        else "n"
    )

    if choice[0] == "y":

        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Include Classic Security Groups")),
            default="n",
        )
        if choice[0] == "y":
            sg_map = Obj.security_groups(
                account_id, region_name, vpc_id, inc_classic_sg=True
            )
        else:
            sg_map = Obj.security_groups(account_id, region_name, vpc_id)

        spec["resources"]["security_group_list"] = []
        sg_names = list(sg_map.keys())

        while True:
            if not sg_names:
                click.echo(highlight_text("\nNo security group available!!!"))
                break

            else:
                click.echo("\nChoose from given security groups: ")
                for ind, name in enumerate(sg_names):
                    dis_name = sg_map[name] + " | " + name
                    click.echo(
                        "\t {}. {}".format(str(ind + 1), highlight_text(dis_name))
                    )

            while True:
                res = click.prompt("\nEnter the index of security group", default=1)
                if (res > len(sg_names)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    sg_name = sg_names[res - 1]
                    sg_id = sg_map[sg_name]
                    dis_name = sg_id + " | " + sg_name

                    security_group = {"security_group_id": sg_id}

                    spec["resources"]["security_group_list"].append(security_group)
                    click.echo("{} selected".format(highlight_text(dis_name)))
                    sg_names.pop(res - 1)
                    break

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to add more security_groups")),
                default="n",
            )
            if choice[0] == "n":
                break

    choice = (
        click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to include subnets")), default="n"
        )
        if (vpc_id and availability_zone)
        else "n"
    )

    if choice[0] == "y":

        subnets = Obj.subnets(account_id, region_name, vpc_id, availability_zone)
        if not subnets:
            click.echo(highlight_text("\nNo subnet available!!!"))

        else:
            click.echo("\nChoose from given subnets")
            for ind, name in enumerate(subnets):
                dis_name = name + " | " + vpc_id
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(dis_name)))

            while True:
                res = click.prompt("\nEnter the index of subnet", default=1)
                if (res > len(subnets)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    subnet_name = subnets[res - 1]
                    spec["resources"]["subnet_id"] = subnet_name
                    dis_name = subnet_name + " | " + vpc_id
                    click.echo("{} selected".format(highlight_text(dis_name)))
                    break

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to enter user data")), default="n"
    )
    if choice[0] == "y":
        user_data = click.prompt("\n\tEnter data", type=str)
        spec["resources"]["user_data"] = user_data

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add any tags")), default="n"
    )
    if choice[0] == "y":
        tags = []
        while True:
            key = click.prompt("\n\tKey")
            value = click.prompt("\tValue")

            tag = {"key": key, "value": value}
            tags.append(tag)
            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to add more tags")), default="n"
            )
            if choice[0] == "n":
                spec["resources"]["tag_list"] = tags
                break

    click.echo("\n\t\t", nl=False)
    click.secho("STORAGE DATA\n", bold=True, underline=True)
    click.secho("\tRoot Disk", bold=True)

    spec["resources"]["block_device_map"] = {}
    root_disk = {}

    if not root_device_name:
        click.echo(
            "\nRoot device is dependent on the machine image. Select a machine image to complete root disk configuration"
        )
    else:
        root_disk["device_name"] = root_device_name
        click.echo(
            "\nDevice for the root disk: {}".format(highlight_text(root_device_name))
        )

    root_disk["size_gb"] = click.prompt("\nEnter the size of disk(in gb)", default=8)

    volume_types = list(aws.VOLUME_TYPE_MAP.keys())
    click.echo("\nChoose from given volume types: ")
    if not volume_types:
        click.echo(highlight_text("\nNo volume type available!!!"))

    else:
        for index, name in enumerate(volume_types):
            click.echo("\t{}. {}".format(index + 1, highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index for Volume Type", default=1)
            if (res > len(volume_types)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                root_disk["volume_type"] = aws.VOLUME_TYPE_MAP[volume_types[res - 1]]
                click.echo("{} selected".format(highlight_text(volume_types[res - 1])))
                break

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to delete disk on termination")),
        default="y",
    )
    root_disk["delete_on_termination"] = True if choice[0] == "y" else False
    spec["resources"]["block_device_map"]["root_disk"] = root_disk

    click.secho("\n\tOther disks", bold=True)
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add more disks")), default="n"
    )

    avl_device_names = list(aws.DeviceMountPoints.keys())
    spec["resources"]["block_device_map"]["data_disk_list"] = []
    while choice[0] == "y":
        disk = {}
        if not avl_device_names:
            click.echo(highlight_text("\nNo device name available!!!"))
            break

        click.echo("\nChoose from given Device Names: ")
        for index, name in enumerate(avl_device_names):
            click.echo("\t{}. {}".format(index + 1, highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index for Device Name", default=1)
            if (res > len(avl_device_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                disk["device_name"] = aws.DeviceMountPoints[avl_device_names[res - 1]]
                click.echo(
                    "{} selected".format(highlight_text(avl_device_names[res - 1]))
                )
                avl_device_names.pop(res - 1)
                break

        click.echo("\nChoose from given volume types: ")
        for index, name in enumerate(volume_types):
            click.echo("\t{}. {}".format(index + 1, highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index for Volume Type", default=1)
            if (res > len(volume_types)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                disk["volume_type"] = aws.VOLUME_TYPE_MAP[volume_types[res - 1]]
                click.echo("{} selected".format(highlight_text(volume_types[res - 1])))
                break

        disk["size_gb"] = click.prompt("\nEnter the size of disk(in gb)", default=8)
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to delete disk on termination")),
            default="y",
        )
        disk["delete_on_termination"] = True if choice[0] == "y" else False

        spec["resources"]["block_device_map"]["data_disk_list"].append(disk)
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more disks")), default="n"
        )

    AwsVmProvider.validate_spec(spec)
    click.secho("\nCreate spec for your AWS VM:\n", underline=True)
    click.echo(highlight_text(yaml.dump(spec, default_flow_style=False)))
