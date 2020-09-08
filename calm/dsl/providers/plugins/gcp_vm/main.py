import click
from ruamel import yaml

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.providers import get_provider_interface
from .constants import GCP as gcp


Provider = get_provider_interface()


class GcpVmProvider(Provider):

    provider_type = "GCP_VM"
    package_name = __name__
    spec_template_file = "gcp_vm_provider_spec.yaml.jinja2"

    @classmethod
    def create_spec(cls):
        client = get_api_client()
        create_spec(client)

    @classmethod
    def get_api_obj(cls):
        """returns object to call gcpprovider specific apis"""

        client = get_api_client()
        return GCP(client.connection)


class GCP:
    def __init__(self, connection):
        self.connection = connection

    def zones(self, account_id, region="undefined"):
        Obj = get_resource_api(gcp.ZONES, self.connection)
        payload = {"filter": "account_uuid=={};region=={}".format(account_id, region)}
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_list = []
        res = res.json()
        for entity in res["entities"]:
            entity_list.append(entity["status"]["name"])

        return entity_list

    def machine_types(self, account_id, zone):
        Obj = get_resource_api(gcp.MACHINE_TYPES, self.connection)
        payload = {"filter": "account_uuid=={};zone=={}".format(account_id, zone)}
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_map = {}
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            selfLink = entity["status"]["resources"]["selfLink"]
            entity_map[name] = selfLink

        return entity_map

    def persistent_disks(self, account_id, zone):
        Obj = get_resource_api(gcp.PERSISTENT_DISKS, self.connection)
        payload = {
            "filter": "account_uuid=={};zone=={};unused==true;private_only==true".format(
                account_id, zone
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_map = {}
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            self_link = entity["status"]["resources"]["selfLink"]
            entity_map[name] = self_link

        return entity_map

    def snapshots(self, account_id, zone):
        Obj = get_resource_api(gcp.SNAPSHOTS, self.connection)
        payload = {
            "filter": "account_uuid=={};zone=={};unused==true;private_only==true".format(
                account_id, zone
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_map = {}
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            selfLink = entity["status"]["resources"]["selfLink"]
            entity_map[name] = selfLink

        return entity_map

    def configured_public_images(self, account_id):
        Obj = get_resource_api("accounts", self.connection)
        res, err = Obj.read(account_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        public_images = res["status"]["resources"]["data"]["public_images"]
        public_image_map = {}
        for entity in public_images:
            selfLink = entity["selfLink"]
            name = selfLink[selfLink.rindex("/") + 1 :]  # noqa
            public_image_map[name] = selfLink

        return public_image_map

    def images(self, account_id, zone):
        Obj = get_resource_api(gcp.DISK_IMAGES, self.connection)
        payload = {
            "filter": "account_uuid=={};zone=={};unused==true;private_only==true".format(
                account_id, zone
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_map = {}
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            selfLink = entity["status"]["resources"]["selfLink"]
            entity_map[name] = selfLink

        return entity_map

    def disk_images(self, account_id, zone):
        """
        Returns gcpImages + gcpSnapshots + configuredPublicImages
        """

        image_map = {}
        image_map.update(self.configured_public_images(account_id))
        image_map.update(self.snapshots(account_id, zone))
        image_map.update(self.images(account_id, zone))

        return image_map

    def networks(self, account_id, zone):
        Obj = get_resource_api(gcp.NETWORKS, self.connection)
        payload = {
            "filter": "account_uuid=={};zone=={};unused==true;private_only==true".format(
                account_id, zone
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_map = {}
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            selfLink = entity["status"]["resources"]["selfLink"]
            entity_map[name] = selfLink

        return entity_map

    def subnetworks(self, account_id, zone):
        Obj = get_resource_api(gcp.SUBNETWORKS, self.connection)
        payload = {
            "filter": "account_uuid=={};zone=={};unused==true;private_only==true".format(
                account_id, zone
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_map = {}
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            selfLink = entity["status"]["resources"]["selfLink"]
            entity_map[name] = selfLink

        return entity_map

    def network_tags(self, account_id):
        Obj = get_resource_api(gcp.FIREWALLS, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        entity_list = []
        res = res.json()
        for entity in res["entities"]:
            targetTags = entity["status"]["resources"].get("targetTags")
            if targetTags:
                entity_list.extend(targetTags)

        return entity_list


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def create_spec(client):

    spec = {}
    Obj = GCP(client.connection)

    # Account Configuration
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

    payload = {"filter": "type==gcp"}
    res, err = client.account.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    gcp_accounts = {}

    for entity in res["entities"]:
        entity_name = entity["metadata"]["name"]
        entity_id = entity["metadata"]["uuid"]
        if entity_id in reg_accounts:
            gcp_accounts[entity_name] = entity_id

    if not gcp_accounts:
        click.echo(
            highlight_text("No gcp account found registered in this project !!!")
        )
        click.echo("Please add one !!!")
        return

    accounts = list(gcp_accounts.keys())
    spec["resources"] = {}

    click.echo("\nChoose from given GCP accounts")
    for ind, name in enumerate(accounts):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        res = click.prompt("\nEnter the index of account to be used", default=1)
        if (res > len(accounts)) or (res <= 0):
            click.echo("Invalid index !!! ")

        else:
            account_name = accounts[res - 1]
            account_id = gcp_accounts[account_name]  # TO BE USED

            spec["resources"]["account_uuid"] = account_id
            click.echo("{} selected".format(highlight_text(account_name)))
            break

    click.echo("\nChoose from given Operating System types:")
    os_types = gcp.OPERATING_SYSTEMS

    for ind, name in enumerate(os_types):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        ind = click.prompt("\nEnter the index of operating system", default=1)
        if (ind > len(os_types)) or (ind <= 0):
            click.echo("Invalid index !!! ")

        else:
            vm_os = os_types[ind - 1]
            click.echo("{} selected".format(highlight_text(vm_os)))
            break

    # VM Configuration
    vm_name = "vm-@@{calm_unique_hash}@@-@@{calm_array_index}@@"
    spec["resources"]["name"] = click.prompt("\nEnter instance name", default=vm_name)

    zone_names = Obj.zones(account_id)
    click.echo("\nChoose from given zones")
    for ind, name in enumerate(zone_names):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        ind = click.prompt("\nEnter the index of zone", default=1)
        if ind > len(zone_names):
            click.echo("Invalid index !!! ")

        else:
            zone = zone_names[ind - 1]  # TO BE USED
            spec["resources"]["zone"] = zone
            click.echo("{} selected".format(highlight_text(zone)))
            break

    machine_type_map = Obj.machine_types(account_id, zone)
    entity_names = list(machine_type_map.keys())
    click.echo("\nChoose from given machine types")
    for ind, name in enumerate(entity_names):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        ind = click.prompt("\nEnter the index of machine type", default=1)
        if ind > len(entity_names):
            click.echo("Invalid index !!! ")

        else:
            machine_type = entity_names[ind - 1]
            click.echo("{} selected".format(highlight_text(machine_type)))
            spec["resources"]["machineType"] = machine_type_map[machine_type]
            break

    # Disk Details
    spec["resources"]["disks"] = get_disks(Obj, account_id, zone)

    # Blank Disk details
    spec["resources"]["blankDisks"] = get_blank_disks(zone)

    # Networks
    spec["resources"]["networkInterfaces"] = get_networks(Obj, account_id, zone)

    # SSH keys
    spec["resources"]["sshKeys"] = get_ssh_keys()
    metadata = {}
    metadata["items"] = []
    block_project_ssh_keys = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to block project-wide SSH keys")),
        default="n",
    )

    if block_project_ssh_keys[0] == "y":
        metadata["items"].append({"value": "true", "key": "block-project-ssh-keys"})

    # Management
    click.echo("\n\t\t", nl=False)
    click.secho("Management (Optional)", bold=True, underline=True)

    # Guest Customization
    guest_customization = {}
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add Customization script")),
        default="n",
    )

    if choice[0] == "y":
        if vm_os == "Linux":
            startup_script = click.prompt("\nEnter Startup script", default="")
            guest_customization = {"startupScript": startup_script}

        else:
            sysprep = click.prompt("\nEnter Sysprep powershell script", default="")
            guest_customization = {"sysprep": sysprep}

    spec["resources"]["guestCustomization"] = guest_customization

    # METADATA TAGS
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add key value pairs to metadata")),
        default="n",
    )
    while choice[0] == "y":
        Key = click.prompt("\n\tKey", default="")
        Value = click.prompt("\tValue", default="")

        metadata["items"].append({"key": Key, "value": Value})
        choice = choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more key value pairs")),
            default="n",
        )

    spec["resources"]["metadata"] = metadata

    # NETWORK TAGS
    network_tags = []
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add network tags")), default="n"
    )
    if choice[0] == "y":
        tag_list = Obj.network_tags(account_id)

    while choice[0] == "y":
        click.echo("\nChoose from given network tags")
        for ind, name in enumerate(tag_list):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of network tag", default=1)
            if ind > len(tag_list):
                click.echo("Invalid index !!! ")

            else:
                network_tag = tag_list[ind - 1]
                tag_list.pop(ind - 1)
                network_tags.append(network_tag)
                click.echo("{} selected".format(highlight_text(network_tag)))
                break

        choice = choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more network tags")),
            default="n",
        )

    spec["resources"]["tags"] = {}
    if network_tags:
        spec["resources"]["tags"] = {"items": network_tags}

    # LABELS
    labels = []
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add labels")), default="n"
    )
    while choice[0] == "y":
        Key = click.prompt("\n\tKey", default="")
        Value = click.prompt("\n\tValue", default="")

        labels.append({"key": Key, "value": Value})
        choice = choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more labels")), default="n"
        )

    spec["resources"]["labels"] = labels

    # API Access Configuration
    click.echo("\n\t\t", nl=False)
    click.secho("API Access", bold=True, underline=True)

    service_account_email = click.prompt("\nEnter the Service Account Email")
    click.echo("\nChoose from given Scopes:")
    scopes = list(gcp.SCOPES.keys())

    for ind, name in enumerate(scopes):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        ind = click.prompt("\nEnter the index of scope", default=1)
        if (ind > len(os_types)) or (ind <= 0):
            click.echo("Invalid index !!! ")

        else:
            scope = scopes[ind - 1]
            click.echo("{} selected".format(highlight_text(scope)))
            break

    service_accounts = []
    # Right now only one account is possible through UI
    service_accounts.append(
        {"scopes": gcp.SCOPES[scope], "email": service_account_email}
    )

    spec["resources"]["serviceAccounts"] = service_accounts

    GcpVmProvider.validate_spec(spec)
    click.secho("\nCreate spec for your GCP VM:\n", underline=True)

    # As it contains ssh keys, So use width=1000 for yaml.dump
    click.echo(highlight_text(yaml.dump(spec, default_flow_style=False, width=1000)))


def get_disks(gcp_obj, account_id, zone):

    gcp_disks = []

    # Boot Disk
    click.echo("\n\t\t", nl=False)
    click.secho("DISKS", bold=True, underline=True)

    click.secho("\n1. BOOT DISK", underline=True)
    # Only persistent disks are allowed in boot disk

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to use existing disk")), default="n"
    )
    choice = True if choice[0] == "y" else False

    # Same set of persistent disk will be used for additional disks too
    persistent_disk_map = gcp_obj.persistent_disks(account_id, zone)
    if choice:
        entity_names = list(persistent_disk_map.keys())
        click.echo("\nChoose from given disks")
        for ind, name in enumerate(entity_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of disk", default=1)
            if ind > len(entity_names):
                click.echo("Invalid index !!! ")

            else:
                disk_name = entity_names[ind - 1]
                click.echo("{} selected".format(highlight_text(disk_name)))
                break

        init_params = {}
        disk_data = {"source": persistent_disk_map[disk_name]}
        persistent_disk_map.pop(disk_name)

    else:
        storage_types = gcp.STORAGE_TYPES
        click.echo("\nChoose from given storage types")
        for ind, name in enumerate(storage_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of storage type", default=1)
            if ind > len(storage_types):
                click.echo("Invalid index !!! ")

            else:
                storage_type = storage_types[ind - 1]
                click.echo("{} selected".format(highlight_text(storage_type)))
                break

        source_image_map = gcp_obj.disk_images(account_id, zone)
        image_names = list(source_image_map.keys())

        click.echo("\nChoose from given source images")
        for ind, name in enumerate(image_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of source images", default=1)
            if ind > len(image_names):
                click.echo("Invalid index !!! ")

            else:
                source_image = image_names[ind - 1]
                source_image_link = source_image_map[source_image]
                click.echo("{} selected".format(highlight_text(source_image)))
                break

        disk_size = click.prompt("\nEnter the size of disk in GB", default=-1)
        disk_type_link = "{}/zones/{}/diskTypes/{}".format(
            gcp.PROJECT_URL, zone, storage_type
        )
        disk_data = {}
        init_params = {
            "diskType": disk_type_link,
            "sourceImage": source_image_link,
            "diskSizeGb": disk_size,
        }

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to delete when instance is deleted")),
        default="n",
    )
    auto_delete = True if choice[0] == "y" else False

    disk_data.update(
        {
            "disk_type": "PERSISTENT",
            "boot": True,
            "autoDelete": auto_delete,
            "initializeParams": init_params,
        }
    )
    gcp_disks.append(disk_data)

    # Additional disks
    click.secho("\n2. ADDITIONAL DISK", underline=True)
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add additional disks")), default="n"
    )

    disk_ind = 0
    while choice[0] == "y":
        click.echo("\n\t\t", nl=False)
        click.secho("ADDITIONAL DISK - {}".format(disk_ind), underline=True)

        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to use existing disk")), default="n"
        )
        choice = True if choice[0] == "y" else False

        if choice:
            entity_names = list(persistent_disk_map.keys())

            click.echo("\nChoose from given disks")
            for ind, name in enumerate(entity_names):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of disk", default=1)
                if ind > len(entity_names):
                    click.echo("Invalid index !!! ")

                else:
                    disk_name = entity_names[ind - 1]
                    click.echo("{} selected".format(highlight_text(disk_name)))
                    break

            init_params = {}
            disk_data = {
                "source": persistent_disk_map[disk_name],
                "disk_type": "PERSISTENT",
            }
            persistent_disk_map.pop(disk_name)  # Pop used disk

        else:
            storage_types = gcp.ADDITIONAL_DISK_STORAGE_TYPES
            click.echo("\nChoose from given storage types")
            for ind, name in enumerate(storage_types):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of storage type", default=1)
                if ind > len(storage_types):
                    click.echo("Invalid index !!! ")

                else:
                    storage_type = storage_types[ind - 1]
                    click.echo("{} selected".format(highlight_text(storage_type)))
                    break

            disk_type_link = "{}/zones/{}/diskTypes/{}".format(
                gcp.PROJECT_URL, zone, storage_type
            )

            if storage_type == "local-ssd":
                interfaces = gcp.DISK_INTERFACES
                click.echo("\nChoose from given interfaces")
                for ind, name in enumerate(interfaces):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt("\nEnter the index of disk interface", default=1)
                    if ind > len(interfaces):
                        click.echo("Invalid index !!! ")

                    else:
                        disk_interface = interfaces[ind - 1]
                        click.echo("{} selected".format(highlight_text(disk_interface)))
                        break

                if disk_interface == "SCSI":
                    disk_interface = ""

                disk_data = {
                    "interface": disk_interface,
                    "disk_type": gcp.STORAGE_DISK_MAP[storage_type],
                }
                init_params = {"diskType": disk_type_link}

            else:
                source_image_map = gcp_obj.disk_images(account_id, zone)
                image_names = list(source_image_map.keys())

                click.echo("\nChoose from given source images")
                for ind, name in enumerate(image_names):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt("\nEnter the index of source images", default=1)
                    if ind > len(image_names):
                        click.echo("Invalid index !!! ")

                    else:
                        source_image = image_names[ind - 1]
                        source_image_link = source_image_map[source_image]
                        click.echo("{} selected".format(highlight_text(source_image)))
                        break

                disk_size = click.prompt("\nEnter the size of disk in GB", default=-1)
                disk_data = {"disk_type": gcp.STORAGE_DISK_MAP[storage_type]}
                init_params = {
                    "diskType": disk_type_link,
                    "sourceImage": source_image_link,
                    "diskSizeGb": disk_size,
                }

        choice = click.prompt(
            "\n{}(y/n)".format(
                highlight_text("Want to delete when instance is deleted")
            ),
            default="n",
        )
        auto_delete = True if choice[0] == "y" else False

        disk_data.update(
            {"boot": False, "autoDelete": auto_delete, "initializeParams": init_params}
        )

        gcp_disks.append(disk_data)
        disk_ind += 1
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more additional disks")),
            default="n",
        )

    return gcp_disks


def get_blank_disks(zone):

    click.echo("\n\t\t", nl=False)
    click.secho("BLANK DISKS", bold=True, underline=True)

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add blank disks")), default="n"
    )

    blank_disks = []
    bdisk_ind = 0
    while choice[0] == "y":
        click.echo("\n\t\t", nl=False)
        click.secho("BLANK DISK - {}".format(bdisk_ind), underline=True)

        storage_types = gcp.STORAGE_TYPES
        click.echo("\nChoose from given storage types")
        for ind, name in enumerate(storage_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of storage type", default=1)
            if ind > len(storage_types):
                click.echo("Invalid index !!! ")

            else:
                storage_type = storage_types[ind - 1]
                click.echo("{} selected".format(highlight_text(storage_type)))
                break

        disk_type_url = "{}/zones/{}/diskTypes/{}".format(
            gcp.PROJECT_URL, zone, storage_type
        )
        disk_name = click.prompt(
            "\nEnter Disk Name",
            default="vm-@@{calm_array_index}@@-@@{calm_time}@@-blankdisk-"
            + str(bdisk_ind + 1),
        )
        disk_size = click.prompt("\nEnter the size of disk in GB", default=-1)
        choice = click.prompt(
            "\n{}(y/n)".format(
                highlight_text("Want to delete when instance is deleted")
            ),
            default="n",
        )
        auto_delete = True if choice[0] == "y" else False

        blank_disks.append(
            {
                "disk_type": disk_type_url,
                "name": disk_name,
                "sizeGb": disk_size,
                "autoDelete": auto_delete,
            }
        )

        bdisk_ind += 1
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more blank disks")),
            default="n",
        )

    return blank_disks


def get_networks(gcp_obj, account_id, zone):

    networks = []
    click.echo("\n\t\t", nl=False)
    click.secho("NETWORKS", bold=True, underline=True)

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add networks")), default="n"
    )

    if choice[0] == "y":
        network_map = gcp_obj.networks(account_id, zone)
        subnetwork_map = gcp_obj.subnetworks(account_id, zone)

    nic_index = 0
    while choice[0] == "y":
        click.echo("\n\t\t", nl=False)
        click.secho("Network {}".format(nic_index), underline=True)

        if not network_map:
            click.secho(highlight_text("\nNo more networks found !!!"))
            break

        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to associate public ip address")),
            default="n",
        )
        associate_public_ip = True if choice[0] == "y" else False

        network_names = list(network_map.keys())
        click.echo("\nChoose from given networks")
        for ind, name in enumerate(network_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of network", default=1)
            if ind > len(network_names):
                click.echo("Invalid index !!! ")

            else:
                network = network_names[ind - 1]
                click.echo("{} selected".format(highlight_text(network)))
                break

        subnetwork_names = list(subnetwork_map.keys())
        click.echo("\nChoose from given subnetworks")
        for ind, name in enumerate(subnetwork_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of subnetwork", default=1)
            if ind > len(subnetwork_names):
                click.echo("Invalid index !!! ")

            else:
                subnetwork = subnetwork_names[ind - 1]
                click.echo("{} selected".format(highlight_text(subnetwork)))
                break

        if associate_public_ip:
            nic_configs = list(gcp.NETWORK_CONFIG_MAP.keys())
            click.echo("\nChoose from given access configuration types")
            for ind, name in enumerate(nic_configs):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt(
                    "\nEnter the index of access configuration  type", default=1
                )
                if ind > len(nic_configs):
                    click.echo("Invalid index !!! ")

                else:
                    access_config_type = nic_configs[ind - 1]
                    click.echo("{} selected".format(highlight_text(access_config_type)))
                    break

            config_name = click.prompt("\nEnter Access Configuration Name", default="")
            networks.append(
                {
                    "network": network_map[network],
                    "subnetwork": subnetwork_map[subnetwork],
                    "accessConfigs": [
                        {"name": config_name, "config_type": access_config_type}
                    ],
                    "associatePublicIP": True,
                }
            )

        else:
            networks.append(
                {
                    "network": network_map[network],
                    "subnetwork": subnetwork_map[subnetwork],
                    "associatePublicIP": False,
                }
            )
        network_map.pop(network)  # Pop out used network
        nic_index += 1
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more networks")), default="n"
        )

    return networks


def get_ssh_keys():
    def check_key_format(key):
        arr = key.split(" ")
        arr_len = len(arr)

        if arr_len != 3:
            return False

        elif not arr[2].find("@"):
            return False

        return True

    def format_key(key):
        arr = key.split(" ")
        username = arr[2].split("@")[0]
        result = "{}:{}".format(username, key)
        return result

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add ssh keys")), default="n"
    )
    ssh_keys = []
    if choice[0] == "y":
        click.echo(
            highlight_text("\n\tFormat: '<protocol> <key-blob> <username@example.com>'")
        )

    while choice[0] == "y":
        key = click.prompt("\nEnter ssh key", default="")
        if key:
            if not check_key_format(key):
                click.echo("Invalid key, look at the format")
                continue

            formated_key = format_key(key)
            ssh_keys.append(formated_key)
            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to add more ssh keys")),
                default="n",
            )
        else:
            break

    return ssh_keys
