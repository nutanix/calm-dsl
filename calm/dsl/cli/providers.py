import click
import json

from .utils import highlight_text
from calm.dsl.providers.api import AHV


def create_ahv_spec(client):

    spec = {}
    Obj = AHV(client.connection)

    spec["name"] = click.prompt("Name of the vm ")
    spec["resources"] = {}

    spec["resources"]["vcpu"] = int(click.prompt("Number of virtual CPU "))
    spec["resources"]["coresPerCPU"] = int(click.prompt("Cores per Virtual CPU "))
    spec["resources"]["memory"] = int(click.prompt("Memory required "))

    imagesNameUUIDMap = Obj.images()
    images = list(imagesNameUUIDMap.keys())

    click.echo(highlight_text("\nEnter the details of disks : \n"))
    click.echo("Images Names are : {}\n". format(images))
    spec["resources"]["disk_list"] = []
    adapterNameIndexMap = {}

    while True:
        image = {}
        image["name"] = click.prompt("Image name ")
        image["device_type"] = click.prompt("Device Type ")
        image["adapter_type"] = click.prompt("Device Bus ")
        image["bootable"] = True if click.prompt("Is it bootable(y/n) ") == "y" else False

        if not adapterNameIndexMap.get(image["adapter_type"]):
            adapterNameIndexMap[image["adapter_type"]] = 0

        disk = {
            "data_source_reference": {
                "name": image["name"],
                "kind": "image",
                "uuid": imagesNameUUIDMap.get(image["name"])
            },
            "device_properties": {
                "device_type": image["device_type"],
                "disk_address": {
                    "device_index":
                        adapterNameIndexMap[image["adapter_type"]],
                    "adapter_type": image["adapter_type"]
                }
            }
        }

        if image["bootable"]:
            spec["resources"]["boot_config"] = {
                "boot_device": {
                    "disk_address": {
                        "device_index":
                            adapterNameIndexMap[image["adapter_type"]],
                        "adapter_type": image["adapter_type"]
                    }
                }
            }

        adapterNameIndexMap[image["adapter_type"]] += 1
        spec["resources"]["disk_list"].append(disk)

        choice = click.prompt(highlight_text("\nWant to add more disks(y/n) "))
        click.echo("")
        if choice[0] == "n":
            break

    choice = click.prompt(highlight_text("Want any virtual disks(y/n) "))
    click.echo("")

    if choice[0] == "y":
        while True:
            vdisk = {}
            vdisk["device_type"] = click.prompt("Device Type ")
            vdisk["adapter_type"] = click.prompt("Device Bus ")
            vdisk["size"] = click.prompt("Size of the disk ")

            if not adapterNameIndexMap.get(vdisk["adapter_type"]):
                adapterNameIndexMap[vdisk["adapter_type"]] = 0

            disk = {
                "device_properties": {
                    "device_type": vdisk["device_type"],
                    "disk_address": {
                        "device_index":
                            adapterNameIndexMap[vdisk["adapter_type"]],
                        "adapter_type": vdisk["adapter_type"]
                    }
                },
                "disk_size_mib": int(vdisk["size"])
            }

            spec["resources"]["disk_list"].append(disk)

            choice = click.prompt(highlight_text("\nWant to add more disks(y/n) "))
            click.echo("")
            if choice[0] == "n":
                break

    choice = click.prompt(highlight_text("Want any network adapters(y/n)"))
    click.echo("")

    if choice[0] == "y":
        subnetNameUUIDMap = Obj.subnets()
        availableNics = list(subnetNameUUIDMap.keys())

        click.echo("Subnet names are {} \n ". format(availableNics))
        spec["resources"]["nic_list"] = []

        while True:
            nic = click.prompt("Enter the nic name ")
            if nic not in availableNics:
                click.echo("choose from existing one !!")

            else:
                nic = {
                    "subnet_reference": {
                        "kind": "subnet",
                        "name": nic,
                        "uuid": subnetNameUUIDMap[nic]
                    }
                }

                spec["resources"]["nic_list"].append(nic)

            choice = click.prompt(highlight_text("\nWant to add more network adpaters(y/n) "))
            click.echo("")
            if choice[0] == "n":
                break

    choice = click.prompt(highlight_text("Want to add guest_customization script (y/n)"))
    click.echo("")

    if choice[0] == "y":
        script_type = click.prompt("Type of script (cloud_init/sys_prep) ")

        if script_type == "cloud_init":
            user_data = click.prompt("Enter the script ")
            spec["resources"]["guest_customization"] = {
                "cloud_init": {
                    "user_data": user_data
                }
            }

        elif script_type == "sys_prep":
            script = {}
            script["unattend_xml"] = click.prompt("Unattend_xml ")
            script["install_type"] = click.prompt("Type of install ")

            spec["resources"]["guest_customization"] = {
                "sys_prep": {
                    "unattend_xml": script["unattend_xml"],
                    "install_type": script["install_type"]
                }
            }

        else:
            click.echo("Invalid script type ")

    click.echo("\nCreate spec \n")
    click.echo(highlight_text(json.dumps(spec, sort_keys=True, indent=4)))
