import click
from ruamel import yaml
import re

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.providers import get_provider_interface
from calm.dsl.tools import StrictDraft7Validator
from calm.dsl.builtins import ref

from .constants import AHV as ahv


Provider = get_provider_interface()


# Implements Provider interface for AHV_VM
class AhvVmProvider(Provider):

    provider_type = "AHV_VM"
    package_name = __name__
    spec_template_file = "ahv_vm_provider_spec.yaml.jinja2"

    @classmethod
    def create_spec(cls):
        client = get_api_client()
        create_spec(client)

    @classmethod
    def update_vm_image_config(cls, spec, disk_packages={}):
        """Ex: disk_packages = {disk_index: vmImageClass}"""
        disk_list = spec["resources"].get("disk_list", [])

        for disk_ind, img_cls in disk_packages.items():
            if disk_ind > len(disk_list):
                raise ValueError("invalid disk address ({})".format(disk_ind))

            disk = disk_list[disk_ind - 1]
            if "data_source_reference" not in disk:
                raise ValueError(
                    "unable to set downloadable image in disk {}".format(disk_ind)
                )

            pkg = img_cls.compile()
            vm_image_type = pkg["options"]["resources"]["image_type"]
            disk_img_type = ahv.IMAGE_TYPES[disk["device_properties"]["device_type"]]

            if vm_image_type != disk_img_type:
                raise TypeError("image type mismatch in disk {}".format(disk_ind))

            # Set the reference of this disk
            disk["data_source_reference"] = ref(img_cls).compile()

    @classmethod
    def get_api_obj(cls):
        client = get_api_client()
        return AHV(client.connection)


class AHV:
    def __init__(self, connection):
        self.connection = connection

    def images(self, image_type="DISK_IMAGE"):
        Obj = get_resource_api(ahv.IMAGES, self.connection)
        res, err = Obj.list()
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        img_name_uuid_map = {}

        for image in res["entities"]:
            img_type = image["status"]["resources"].get("image_type", None)

            # Ignoring images, if they don't have any image type(Ex: Karbon Image)
            if not img_type:
                continue

            if img_type == image_type:
                img_name_uuid_map[image["status"]["name"]] = image["metadata"]["uuid"]

        return img_name_uuid_map

    def subnets(self, payload):
        Obj = get_resource_api(ahv.SUBNETS, self.connection)
        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        return res.json()

    def groups(self, payload):
        Obj = get_resource_api(ahv.GROUPS, self.connection)

        if not payload:
            raise Exception("no payload")

        return Obj.create(payload)

    def categories(self):

        payload = {
            "entity_type": "category",
            "filter_criteria": "name!=CalmApplication;name!=CalmDeployment;name!=CalmService;name!=CalmPackage",
            "grouping_attribute": "abac_category_key",
            "group_sort_attribute": "name",
            "group_count": 60,
            "group_attributes": [
                {"attribute": "name", "ancestor_entity_type": "abac_category_key"}
            ],
            "group_member_count": 1000,
            "group_member_offset": 0,
            "group_member_sort_attribute": "value",
            "group_member_attributes": [{"attribute": "value"}],
            "query_name": "prism:CategoriesQueryModel",
        }

        response, err = self.groups(payload)
        categories = []

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        response = response.json()
        for group in response["group_results"]:

            key = group["group_summaries"]["sum:name"]["values"][0]["values"][0]

            for entity in group["entity_results"]:
                value = entity["data"][0]["values"][0]["values"][0]
                categories.append({"key": key, "value": value})

        return categories


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def create_spec(client):

    spec = {}
    Obj = AHV(client.connection)
    schema = AhvVmProvider.get_provider_spec()
    path = []  # Path to the key
    option = []  # Any option occured during finding key

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
    subnets_list = []
    for subnet in project["status"]["project_status"]["resources"][
        "subnet_reference_list"
    ]:
        subnets_list.append(subnet["name"])

    click.echo("")
    path.append("name")
    spec["name"] = get_field(
        schema,
        path,
        option,
        default="vm_@@{calm_application_name}@@-@@{calm_array_index}@@",
    )

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add some categories")), default="n"
    )
    if choice[0] == "y":
        categories = Obj.categories()

        if not categories:
            click.echo("\n{}\n".format(highlight_text("No Category present")))

        else:
            click.echo("\n Choose from given categories: \n")
            for ind, group in enumerate(categories):
                category = "{}:{}".format(group["key"], group["value"])
                click.echo("\t {}. {} ".format(str(ind + 1), highlight_text(category)))

            result = {}
            while True:

                while True:
                    index = click.prompt("\nEnter the index of category", default=1)
                    if (index > len(categories)) or (index <= 0):
                        click.echo("Invalid index !!! ")

                    else:
                        break

                group = categories[index - 1]
                key = group["key"]
                if result.get(key) is not None:
                    click.echo(
                        "Category corresponding to key {} already exists ".format(key)
                    )
                    choice = click.prompt(
                        "\n{}(y/n)".format(highlight_text("Want to replace old one")),
                        default="n",
                    )
                    if choice[0] == "y":
                        result[key] = group["value"]
                        click.echo(
                            highlight_text(
                                "category with (key = {}) updated".format(key)
                            )
                        )

                else:
                    category = "{}:{}".format(group["key"], group["value"])
                    click.echo("{} selected".format(highlight_text(category)))
                    result[key] = group["value"]

                choice = click.prompt(
                    "\n{}(y/n)".format(
                        highlight_text("Want to add more categories(y/n)")
                    ),
                    default="n",
                )
                if choice[0] == "n":
                    break

            spec["categories"] = result

    spec["resources"] = {}
    path[-1] = "resources"

    path.append("num_sockets")
    click.echo("")
    spec["resources"]["num_sockets"] = get_field(
        schema, path, option, default=1, msg="Enter vCPUs count"
    )

    path[-1] = "num_vcpus_per_socket"
    click.echo("")
    spec["resources"]["num_vcpus_per_socket"] = get_field(
        schema, path, option, default=1, msg="Enter Cores per vCPU count"
    )

    path[-1] = "memory_size_mib"
    click.echo("")
    spec["resources"]["memory_size_mib"] = (
        get_field(schema, path, option, default=1, msg="Enter Memory(GiB)") * 1024
    )

    click.secho("\nAdd some disks:\n", fg="blue", bold=True)

    spec["resources"]["disk_list"] = []
    spec["resources"]["boot_config"] = {}
    path[-1] = "disk_list"
    option.append("AHV Disk")

    adapterNameIndexMap = {}
    image_index = 0
    while True:
        image = {}
        image_index += 1
        click.secho(
            "\nImage Device {}".format(str(image_index)), bold=True, underline=True
        )

        click.echo("\nChoose from given Device Types :")
        device_types = list(ahv.DEVICE_TYPES.keys())
        for index, device_type in enumerate(device_types):
            click.echo("\t{}. {}".format(index + 1, highlight_text(device_type)))

        while True:
            res = click.prompt("\nEnter the index for Device Type", default=1)
            if (res > len(device_types)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                image["device_type"] = ahv.DEVICE_TYPES[device_types[res - 1]]
                click.echo("{} selected".format(highlight_text(image["device_type"])))
                break

        click.echo("\nChoose from given Device Bus :")
        device_bus_list = list(ahv.DEVICE_BUS[image["device_type"]].keys())
        for index, device_bus in enumerate(device_bus_list):
            click.echo("\t{}. {}".format(index + 1, highlight_text(device_bus)))

        while True:
            res = click.prompt("\nEnter the index for Device Bus", default=1)
            if (res > len(device_bus_list)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                image["adapter_type"] = ahv.DEVICE_BUS[image["device_type"]][
                    device_bus_list[res - 1]
                ]
                click.echo("{} selected".format(highlight_text(image["adapter_type"])))
                break

        # Add image details
        imagesNameUUIDMap = Obj.images(ahv.IMAGE_TYPES[image["device_type"]])
        images = list(imagesNameUUIDMap.keys())

        while True:
            if not images:
                click.echo("\n{}".format(highlight_text("No image present")))
                image["name"] = ""
                break

            click.echo("\nChoose from given images: \n")
            for ind, name in enumerate(images):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            res = click.prompt("\nEnter the index of image", default=1)
            if (res > len(images)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                image["name"] = images[res - 1]
                click.echo("{} selected".format(highlight_text(image["name"])))
                break

        image["bootable"] = click.prompt("\nIs it bootable(y/n)", default="y")

        if not adapterNameIndexMap.get(image["adapter_type"]):
            adapterNameIndexMap[image["adapter_type"]] = 0

        disk = {
            "data_source_reference": {},
            "device_properties": {
                "device_type": image["device_type"],
                "disk_address": {
                    "device_index": adapterNameIndexMap[image["adapter_type"]],
                    "adapter_type": image["adapter_type"],
                },
            },
        }

        # If image exists, then update data_source_reference
        if image["name"]:
            disk["data_source_reference"] = {
                "name": image["name"],
                "kind": "image",
                "uuid": imagesNameUUIDMap.get(image["name"], ""),
            }

        if image["bootable"]:
            spec["resources"]["boot_config"] = {
                "boot_device": {
                    "disk_address": {
                        "device_index": adapterNameIndexMap[image["adapter_type"]],
                        "adapter_type": image["adapter_type"],
                    }
                }
            }

        adapterNameIndexMap[image["adapter_type"]] += 1
        spec["resources"]["disk_list"].append(disk)

        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more disks")), default="n"
        )
        if choice[0] == "n":
            break

    click.echo("\nChoose from given Boot Type :")
    boot_types = list(ahv.BOOT_TYPES.keys())
    for index, boot_type in enumerate(boot_types):
        click.echo("\t{}. {}".format(index + 1, highlight_text(boot_type)))

    while True:
        res = click.prompt("\nEnter the index for Boot Type", default=1)
        if (res > len(boot_types)) or (res <= 0):
            click.echo("Invalid index !!! ")

        else:
            boot_type = ahv.BOOT_TYPES[boot_types[res - 1]]
            if boot_type == ahv.BOOT_TYPES["UEFI"]:
                spec["resources"]["boot_config"]["boot_type"] = boot_type
            click.echo("{} selected".format(highlight_text(boot_type)))
            break

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want any virtual disks")), default="n"
    )
    if choice[0] == "y":
        option[-1] = "AHV VDisk"

        while True:
            vdisk = {}

            click.echo("\nChoose from given Device Types: ")
            device_types = list(ahv.DEVICE_TYPES.keys())
            for index, device_type in enumerate(device_types):
                click.echo("\t{}. {}".format(index + 1, highlight_text(device_type)))

            while True:
                res = click.prompt("\nEnter the index for Device Type", default=1)
                if (res > len(device_types)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    vdisk["device_type"] = ahv.DEVICE_TYPES[device_types[res - 1]]
                    click.echo(
                        "{} selected".format(highlight_text(vdisk["device_type"]))
                    )
                    break

            click.echo("\nChoose from given Device Bus :")
            device_bus_list = list(ahv.DEVICE_BUS[vdisk["device_type"]].keys())
            for index, device_bus in enumerate(device_bus_list):
                click.echo("\t{}. {}".format(index + 1, highlight_text(device_bus)))

            while True:
                res = click.prompt("\nEnter the index for Device Bus: ", default=1)
                if (res > len(device_bus_list)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    vdisk["adapter_type"] = ahv.DEVICE_BUS[vdisk["device_type"]][
                        device_bus_list[res - 1]
                    ]
                    click.echo(
                        "{} selected".format(highlight_text(vdisk["adapter_type"]))
                    )
                    break

            path.append("disk_size_mib")

            if vdisk["device_type"] == ahv.DEVICE_TYPES["DISK"]:
                click.echo("")
                msg = "Enter disk size(GB)"
                vdisk["size"] = get_field(schema, path, option, default=8, msg=msg)
                vdisk["size"] = vdisk["size"] * 1024
            else:
                vdisk["size"] = 0

            if not adapterNameIndexMap.get(vdisk["adapter_type"]):
                adapterNameIndexMap[vdisk["adapter_type"]] = 0

            disk = {
                "device_properties": {
                    "device_type": vdisk["device_type"],
                    "disk_address": {
                        "device_index": adapterNameIndexMap[vdisk["adapter_type"]],
                        "adapter_type": vdisk["adapter_type"],
                    },
                },
                "disk_size_mib": vdisk["size"],
            }

            spec["resources"]["disk_list"].append(disk)
            path = path[:-1]

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to add more virtual disks")),
                default="n",
            )
            if choice[0] == "n":
                break

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want any network adapters")), default="n"
    )
    if choice[0] == "y":

        if subnets_list:
            payload = {"filter": "(name=={})".format(",name==".join(subnets_list))}
        else:
            payload = {}

        nics = Obj.subnets(payload)
        nics = nics["entities"]

        if not nics:
            click.echo("\n{}".format(highlight_text("No network adapter present")))

        else:
            click.echo("\nChoose from given subnets:")
            for ind, nic in enumerate(nics):
                click.echo(
                    "\t {}. {}".format(
                        str(ind + 1), highlight_text(nic["status"]["name"])
                    )
                )

            spec["resources"]["nic_list"] = []
            while True:
                nic_config = {}
                while True:
                    res = click.prompt("\nEnter the index of subnet's name", default=1)
                    if (res > len(nics)) or (res <= 0):
                        click.echo("Invalid index !!!")

                    else:
                        nic_config = nics[res - 1]
                        click.echo(
                            "{} selected".format(
                                highlight_text(nic_config["status"]["name"])
                            )
                        )
                        break

                # Check for static vlan
                nic = {}
                if nic_config["status"]["resources"].get("ip_config"):
                    choice = click.prompt(
                        "\n{}(y/n)".format(highlight_text("Use static Ip")), default="n"
                    )
                    if choice[0] == "y":
                        ip = click.prompt("\nEnter Ip")
                        nic = {"ip_endpoint_list": [{"ip": ip}]}

                nic.update(
                    {
                        "subnet_reference": {
                            "kind": "subnet",
                            "name": nic_config["status"]["name"],
                            "uuid": nic_config["metadata"]["uuid"],
                        }
                    }
                )

                spec["resources"]["nic_list"].append(nic)
                choice = click.prompt(
                    "\n{}(y/n)".format(
                        highlight_text("Want to add more network adpaters")
                    ),
                    default="n",
                )
                if choice[0] == "n":
                    break

    path = ["resources"]
    option = []

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add Customization script")),
        default="n",
    )
    if choice[0] == "y":
        path.append("guest_customization")
        script_types = ahv.GUEST_CUSTOMIZATION_SCRIPT_TYPES

        click.echo("\nChoose from given script types ")
        for index, scriptType in enumerate(script_types):
            click.echo("\t {}. {}".format(str(index + 1), highlight_text(scriptType)))

        while True:
            index = click.prompt("\nEnter the index for type of script", default=1)
            if (index > len(script_types)) or (index <= 0):
                click.echo("Invalid index !!!")
            else:
                script_type = script_types[index - 1]
                click.echo("{} selected".format(highlight_text(script_type)))
                break

        if script_type == "cloud_init":
            option.append("AHV CLOUD INIT Script")
            path = path + ["cloud_init", "user_data"]

            click.echo("")
            user_data = get_field(schema, path, option, default="")
            spec["resources"]["guest_customization"] = {
                "cloud_init": {"user_data": user_data}
            }

        elif script_type == "sysprep":
            option.append("AHV Sys Prep Script")
            path.append("sysprep")
            script = {}

            install_types = ahv.SYS_PREP_INSTALL_TYPES
            click.echo("\nChoose from given install types ")
            for index, value in enumerate(install_types):
                click.echo("\t {}. {}".format(str(index + 1), highlight_text(value)))

            while True:
                index = click.prompt(
                    "\nEnter the index for type of installing script", default=1
                )
                if (index > len(install_types)) or (index <= 0):
                    click.echo("Invalid index !!!")
                else:
                    install_type = install_types[index - 1]
                    click.echo("{} selected\n".format(highlight_text(install_type)))
                    break

            script["install_type"] = install_type

            path.append("unattend_xml")
            script["unattend_xml"] = get_field(schema, path, option, default="")

            sysprep_dict = {
                "unattend_xml": script["unattend_xml"],
                "install_type": script["install_type"],
            }

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to join a domain")), default="n"
            )

            if choice[0] == "y":
                domain = click.prompt("\nEnter Domain Name", default="")
                dns_ip = click.prompt("\nEnter DNS IP", default="")
                dns_search_path = click.prompt("\nEnter DNS Search Path", default="")
                credential = click.prompt("\nEnter Credential", default="")

                sysprep_dict.update(
                    {
                        "is_domain": True,
                        "domain": domain,
                        "dns_ip": dns_ip,
                        "dns_search_path": dns_search_path,
                    }
                )

                if credential:  # Review after CALM-15575 is resolved
                    sysprep_dict["domain_credential_reference"] = {
                        "kind": "app_credential",
                        "name": credential,
                    }

            spec["resources"]["guest_customization"] = {"sysprep": sysprep_dict}

    AhvVmProvider.validate_spec(spec)  # Final validation (Insert some default's value)
    click.echo("\nCreate spec for your AHV VM:\n")
    click.echo(highlight_text(yaml.dump(spec, default_flow_style=False)))


def find_schema(schema, path, option):
    if len(path) == 0:
        return {}

    indPath = 0
    indOpt = 0

    pathLength = len(path)

    while indPath < pathLength:

        if schema.get("anyOf") is not None:

            resDict = None
            for optionDict in schema["anyOf"]:
                if optionDict["title"] == option[indOpt]:
                    resDict = optionDict
                    break

            if not resDict:
                print("Not a valid key")
            else:
                schema = resDict
                indOpt = indOpt + 1

        elif schema["type"] == "array":
            schema = schema["items"]

        else:
            schema = schema["properties"]
            schema = schema[path[indPath]]
            indPath = indPath + 1

    return schema


def validate_field(schema, path, options, spec):

    keySchema = find_schema(schema, path, options)
    return StrictDraft7Validator(keySchema).is_valid(spec)


def get_field(schema, path, options, type=str, default=None, msg=None):

    field = path[-1]
    field = field.replace("_", " ")
    field = re.sub(r"(?<=\w)([A-Z])", r" \1", field)
    field = field.capitalize()

    if msg is None:
        msg = "Enter {}".format(field)

    data = ""
    while True:
        if not default:
            data = click.prompt(msg, type=type)

        else:
            data = click.prompt(msg, default=default)

        if not validate_field(schema, path, options, data):
            click.echo("data incorrect. Enter again")

        else:
            break

    return data
