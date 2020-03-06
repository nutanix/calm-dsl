import click
from ruamel import yaml
import re
import json
import sys

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.providers import get_provider_interface
from calm.dsl.tools import StrictDraft7Validator, get_logging_handle
from calm.dsl.builtins import ref
from calm.dsl.store import Cache

from .constants import AHV as ahv

LOG = get_logging_handle(__name__)
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
    def get_runtime_editables(
        cls, sub_editable_spec, project_id, substrate_spec, vm_img_map={}
    ):
        """Fetch runtime editables at runtime"""

        client = get_api_client()
        Obj = AHV(client.connection)

        runtime_spec = sub_editable_spec["value"].get("spec", {})
        if runtime_spec.get("resources") or runtime_spec.get("categories"):
            click.secho(
                "\n-- Substrate '{}' --".format(
                    highlight_text(
                        sub_editable_spec["context"] + "." + sub_editable_spec["name"]
                    )
                )
            )

        else:
            # Nothing to get input
            return

        sub_create_spec = substrate_spec["create_spec"]
        downloadable_images = list(vm_img_map.keys())
        vm_os = substrate_spec["os_type"]

        # NAME
        vm_name = runtime_spec.get("name", None)
        if vm_name:
            vm_name = click.prompt(
                "\nName of vm [{}]".format(highlight_text(vm_name)),
                default=vm_name,
                show_default=False,
            )
            runtime_spec["name"] = vm_name

        # Check for categories
        if "categories" in runtime_spec.keys():
            avl_categories = {}
            if runtime_spec["categories"]:
                avl_categories = json.loads(runtime_spec["categories"])

        resources = runtime_spec.get("resources", {})

        # NICS
        nic_list = resources.get("nic_list", {})
        # Normal Nic for now
        if nic_list:
            click.secho("\n\tNICS data\n", underline=True)
            res, err = client.project.read(project_id)
            if err:
                raise Exception("[{}] - {}".format(err["code"], err["error"]))

            project = res.json()
            subnets_name_id_map = {}
            for subnet in project["status"]["project_status"]["resources"][
                "subnet_reference_list"
            ]:
                subnets_name_id_map[subnet["name"]] = subnet["uuid"]

            click.echo("Choose from given subnets:")
            for ind, name in enumerate(subnets_name_id_map.keys()):
                click.echo("\t {}. {}".format(str(ind + 1), name))

            for nic_index, nic_data in nic_list.items():
                click.echo("\n--Nic {} -- ".format(nic_index))
                nic_uuid = nic_data["subnet_reference"].get("uuid")
                nic_name = Cache.get_entity_name("AHV_SUBNET", nic_uuid)

                if nic_uuid.startswith("@@") and nic_uuid.endswith("@@"):
                    # It will be macro
                    var_name = nic_uuid[3:-8]
                    nic_name = "@@{" + var_name + "}@@"

                new_val = click.prompt(
                    "Subnet for nic {} [{}]".format(
                        nic_index, highlight_text(nic_name)
                    ),
                    default=nic_name,
                    show_default=False,
                )
                if new_val.startswith("@@") and new_val.endswith("@@"):
                    # Macro case
                    var_name = new_val[3:-3]
                    nic_uuid = "@@{" + var_name + ".uuid}@@"
                    nic_data["subnet_reference"].update({"uuid": nic_uuid, "name": ""})

                else:
                    nic_data["subnet_reference"].update(
                        {"name": new_val, "uuid": subnets_name_id_map[new_val]}
                    )

        # DISKS
        disk_list = resources.get("disk_list", {})
        bp_disks = sub_create_spec["resources"]["disk_list"]
        if disk_list:
            click.secho("\n\tDISKS data", underline=True)
            for disk_ind, disk_data in disk_list.items():
                click.echo("\n--Data Disk {} --".format(disk_ind))
                bp_disk_data = bp_disks[int(disk_ind)]

                if "device_properties" in disk_data.keys():
                    device_prop = disk_data.get("device_properties", {})
                    device_type = device_prop.get("device_type", None)

                    if device_type:
                        click.echo("\nChoose from given Device Types :")
                        device_types = list(ahv.DEVICE_TYPES.keys())
                        for ind, dt in enumerate(device_types):
                            click.echo("\t{}. {}".format(ind + 1, dt))

                        new_val = click.prompt(
                            "Device Type name for data disk {} [{}]".format(
                                disk_ind, highlight_text(device_type)
                            ),
                            type=click.Choice(device_types),
                            show_choices=False,
                            default=device_type,
                            show_default=False,
                        )

                        device_type = ahv.DEVICE_TYPES[new_val]
                        # Change the data dict
                        device_prop["device_type"] = device_type

                    else:
                        device_type = bp_disk_data["device_properties"]["device_type"]

                    disk_address = device_prop.get("disk_address", {})
                    device_bus = disk_address.get("adapter_type", None)

                    if device_bus:
                        device_bus_list = list(ahv.DEVICE_BUS[device_type].keys())
                        if device_bus not in device_bus_list:
                            device_bus = device_bus_list[0]

                        click.echo("\nChoose from given Device Buses :")
                        for ind, db in enumerate(device_bus_list):
                            click.echo("\t{}. {}".format(ind + 1, db))

                        new_val = click.prompt(
                            "Device Bus for data disk {} [{}]".format(
                                disk_ind, highlight_text(device_bus)
                            ),
                            type=click.Choice(device_bus_list),
                            show_choices=False,
                            default=device_bus,
                            show_default=False,
                        )

                        device_bus = new_val if new_val else device_bus
                        device_prop["disk_address"]["adapter_type"] = ahv.DEVICE_BUS[
                            device_type
                        ][device_bus]

                else:
                    device_type = bp_disk_data["device_properties"]["device_type"]

                is_data_ref_present = "data_source_reference" in disk_data.keys()
                is_size_present = "disk_size_mib" in disk_data.keys()

                if is_data_ref_present and is_size_present:
                    # Check for the operation
                    operation_list = ahv.OPERATION_TYPES[device_type]
                    click.echo("\nChoose from given Operation:")
                    for ind, op in enumerate(operation_list):
                        click.echo("\t{}. {}".format(ind + 1, op))

                    # TODO choose default operation wisely
                    op = operation_list[0]
                    op = click.prompt(
                        "Enter the operation type for data disk {} [{}]".format(
                            disk_ind, highlight_text(op)
                        ),
                        default=op,
                        type=click.Choice(operation_list),
                        show_choices=False,
                        show_default=False,
                    )

                    if op == "CLONE_FROM_IMAGE":
                        data_source_ref = (
                            disk_data["data_source_reference"]
                            if disk_data.get("data_source_reference")
                            else {}
                        )

                        imagesNameUUIDMap = Obj.images(ahv.IMAGE_TYPES[device_type])
                        images = list(imagesNameUUIDMap.keys())

                        if not (images or downloadable_images):
                            LOG.error(
                                "No images found for device type: {}".format(
                                    device_type
                                )
                            )
                            sys.exit(-1)

                        img_name = data_source_ref.get("name", images[0])
                        if (img_name not in images) and (
                            img_name not in downloadable_images
                        ):
                            img_name = images[0] if images else downloadable_images[0]

                        click.echo("\nChoose from given images:")
                        if images:
                            click.secho("Disk Images", bold=True)
                            for ind, name in enumerate(images):
                                click.echo("\t {}. {}".format(str(ind + 1), name))

                        if downloadable_images:
                            click.secho("Downloadable Images", bold=True)
                            for ind, name in enumerate(downloadable_images):
                                click.echo("\t {}. {}".format(str(ind + 1), name))

                        all_images = images + downloadable_images
                        img_name = click.prompt(
                            "\nImage for data disk {} [{}]".format(
                                disk_ind, highlight_text(img_name)
                            ),
                            default=img_name,
                            type=click.Choice(all_images),
                            show_choices=False,
                            show_default=False,
                        )

                        is_normal_image = "y"
                        if (img_name in images) and (img_name in downloadable_images):
                            is_normal_image = click.prompt(
                                "Is it Disk Image (y/n) [{}]".format(
                                    highlight_text("y")
                                ),
                                default="y",
                                show_default=False,
                                type=click.Choice(["y", "n"]),
                                show_choices=False,
                            )

                        elif img_name in images:
                            is_normal_image = "y"

                        else:
                            is_normal_image = "n"

                        if is_normal_image == "y":
                            disk_data["data_source_reference"] = {
                                "kind": "image",
                                "name": img_name,
                                "uuid": imagesNameUUIDMap[img_name],
                            }

                        else:
                            disk_data["data_source_reference"] = {
                                "kind": "app_package",
                                "name": img_name,
                                "uuid": vm_img_map[img_name],
                            }

                    elif op == "ALLOCATE_STORAGE_CONTAINER":
                        size = disk_data.get("disk_size_mib", 0)
                        size = size / 1024

                        size = click.prompt(
                            "\nSize of disk {} (GiB) [{}]".format(
                                disk_ind, highlight_text(size)
                            ),
                            default=size,
                            show_default=False,
                        )
                        disk_data["disk_size_mib"] = size * 1024

                    elif op == "EMPTY_CDROM":
                        disk_data["data_source_reference"] = None
                        disk_data["disk_size_mib"] = 0

                elif is_data_ref_present:
                    data_source_ref = (
                        disk_data["data_source_reference"]
                        if disk_data.get("data_source_reference")
                        else {}
                    )

                    imagesNameUUIDMap = Obj.images(ahv.IMAGE_TYPES[device_type])
                    images = list(imagesNameUUIDMap.keys())

                    if not (images or downloadable_images):
                        LOG.error(
                            "No images found for device type: {}".format(device_type)
                        )
                        sys.exit(-1)

                    img_name = data_source_ref.get("name", images[0])
                    if (img_name not in images) and (
                        img_name not in downloadable_images
                    ):
                        img_name = images[0] if images else downloadable_images[0]

                    click.echo("\nChoose from given images:")
                    if images:
                        click.secho("Disk Images", bold=True)
                        for ind, name in enumerate(images):
                            click.echo("\t {}. {}".format(str(ind + 1), name))

                    if downloadable_images:
                        click.secho("Downloadable Images", bold=True)
                        for ind, name in enumerate(downloadable_images):
                            click.echo("\t {}. {}".format(str(ind + 1), name))

                    all_images = images + downloadable_images
                    img_name = click.prompt(
                        "\nImage for data disk {} [{}]".format(
                            disk_ind, highlight_text(img_name)
                        ),
                        default=img_name,
                        type=click.Choice(all_images),
                        show_choices=False,
                        show_default=False,
                    )

                    is_normal_image = "y"
                    if (img_name in images) and (img_name in downloadable_images):
                        is_normal_image = click.prompt(
                            "Is it Disk Image (y/n) [{}]".format(highlight_text("y")),
                            default="y",
                            show_default=False,
                            type=click.Choice(["y", "n"]),
                            show_choices=False,
                        )

                    elif img_name in images:
                        is_normal_image = "y"

                    else:
                        is_normal_image = "n"

                    if is_normal_image == "y":
                        disk_data["data_source_reference"] = {
                            "kind": "image",
                            "name": img_name,
                            "uuid": imagesNameUUIDMap[img_name],
                        }

                    else:
                        disk_data["data_source_reference"] = {
                            "kind": "app_package",
                            "name": img_name,
                            "uuid": vm_img_map[img_name],
                        }

                elif is_size_present:
                    size = disk_data.get("disk_size_mib", 0)
                    size = int(size / 1024)

                    size = click.prompt(
                        "\nSize of disk {} (GiB) [{}]".format(
                            disk_ind, highlight_text(size)
                        ),
                        default=size,
                        show_default=False,
                    )
                    disk_data["disk_size_mib"] = size * 1024

        # num_sockets
        vCPUs = resources.get("num_sockets", None)
        if vCPUs:
            vCPUS = click.prompt(
                "\nvCPUS for the vm [{}]".format(highlight_text(vCPUs)),
                default=vCPUs,
                show_default=False,
            )
            resources["num_sockets"] = vCPUS

        # num_vcpu_per_socket
        cores_per_vcpu = resources.get("num_vcpus_per_socket", None)
        if cores_per_vcpu:
            cores_per_vcpu = click.prompt(
                "\nCores per vCPU for the vm [{}]".format(
                    highlight_text(cores_per_vcpu)
                ),
                default=cores_per_vcpu,
                show_default=False,
            )
            resources["num_vcpus_per_socket"] = cores_per_vcpu

        # memory
        memory_size_mib = resources.get("memory_size_mib", None)
        if memory_size_mib:
            memory_size_mib = int(memory_size_mib / 1024)
            memory_size_mib = click.prompt(
                "\nMemory(GiB) for the vm [{}]".format(highlight_text(memory_size_mib)),
                default=memory_size_mib,
                show_default=False,
            )
            resources["memory_size_mib"] = memory_size_mib * 1024

        # serial ports
        serial_ports = resources.get("serial_port_list", {})
        click.secho("\n\tSerial Ports data", underline=True)
        for ind, port_data in serial_ports.items():
            is_connected = port_data["is_connected"]
            new_val = "y" if is_connected else "n"

            new_val = click.prompt(
                "\nConnection status for serial port {} (y/n) [{}]".format(
                    ind, highlight_text(new_val)
                ),
                default=new_val,
                show_default=False,
                type=click.Choice(["y", "n"]),
                show_choices=False,
            )

            if new_val == "y":
                port_data["is_connected"] = True

            else:
                port_data["is_connected"] = False

        # Guest Customization
        if "guest_customization" in resources.keys():
            click.secho("\n\tGuest Customization", underline=True)
            guest_cus = (
                resources["guest_customization"]
                if resources.get("guest_customization")
                else {}
            )

            choice = click.prompt(
                "\nEdit Guest Customization (y/n) [{}]".format(highlight_text("n")),
                default="n",
                show_default=False,
                type=click.Choice(["y", "n"]),
                show_choices=False,
            )

            if choice == "y":
                if vm_os == ahv.OPERATING_SYSTEM["LINUX"]:
                    cloud_init = (
                        guest_cus["cloud_init"] if guest_cus.get("cloud_init") else {}
                    )

                    user_data = cloud_init.get("user_data", "")
                    user_data = click.prompt(
                        "\nUser data for guest customization for VM [{}]".format(
                            highlight_text(user_data)
                        ),
                        default=user_data,
                        show_default=False,
                    )
                    resources["guest_customization"]["cloud_init"][
                        "user_data"
                    ] = json.dumps(user_data)

                else:
                    sysprep = guest_cus["sysprep"] if guest_cus.get("sysprep") else {}
                    choice = click.prompt(
                        "Want to enter sysprep data (y/n) [{}]".format(
                            highlight_text("n")
                        ),
                        default="n",
                        show_default=False,
                        type=click.Choice(["y", "n"]),
                        show_choices=False,
                    )

                    if choice[0] == "y":

                        install_types = ahv.SYS_PREP_INSTALL_TYPES
                        install_type = sysprep.get("install_type", install_types[0])

                        click.echo("\nChoose from given install types ")
                        for index, value in enumerate(install_types):
                            click.echo("\t {}. {}".format(str(index + 1), value))

                        install_type = click.prompt(
                            "Install type [{}]".format(highlight_text(install_type)),
                            default=install_type,
                            show_default=False,
                            type=click.Choice([install_types]),
                            show_choices=False,
                        )
                        sysprep["install_type"] = install_type

                        unattend_xml = sysprep.get("unattend_xml", "")
                        unattend_xml = click.prompt(
                            "\nUnattend XML", default=highlight_text(unattend_xml)
                        )
                        sysprep["unattend_xml"] = unattend_xml

                        is_domain = "y" if sysprep.get("is_domain", False) else "n"
                        is_domain = click.prompt(
                            "\nJoin a domain (y/n) [{}]".format(
                                highlight_text(is_domain)
                            ),
                            default=is_domain,
                            show_default=False,
                            type=click.Choice(["y", "n"]),
                            show_choices=False,
                        )
                        is_domain = True if is_domain[0] == "y" else False
                        sysprep["is_domain"] = is_domain

                        if is_domain:
                            domain = sysprep.get("domain", "")
                            domain = click.prompt(
                                "\nDomain name [{}]".format(highlight_text(domain)),
                                default=domain,
                                show_default=False,
                            )
                            sysprep["domain"] = domain

                            dns_ip = sysprep.get("dns_ip", "")
                            dns_ip = click.prompt(
                                "\nDNS IP [{}]".format(highlight_text(dns_ip)),
                                default=dns_ip,
                                show_default=False,
                            )
                            sysprep["dns_ip"] = dns_ip

                            dns_search_path = sysprep.get("dns_search_path", "")
                            dns_search_path = click.prompt(
                                "\nDNS Search Path [{}]".format(
                                    highlight_text(dns_search_path)
                                ),
                                default=dns_search_path,
                                show_default=False,
                            )
                            sysprep["dns_search_path"] = dns_search_path

                        # TODO add support for credential too


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
