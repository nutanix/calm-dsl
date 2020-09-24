import click
from ruamel import yaml

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.providers import get_provider_interface
from .constants import AZURE as azure


Provider = get_provider_interface()


class AzureVmProvider(Provider):

    provider_type = "AZURE_VM"
    package_name = __name__
    spec_template_file = "azure_vm_provider_spec.yaml.jinja2"

    @classmethod
    def create_spec(cls):
        client = get_api_client()
        create_spec(client)

    @classmethod
    def get_api_obj(cls):
        """returns object to call azure provider specific apis"""

        client = get_api_client()
        return Azure(client.connection)


class Azure:
    def __init__(self, connection):
        self.connection = connection

    def resource_groups(self, account_id):
        Obj = get_resource_api(azure.RESOURCE_GROUPS, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res_groups = []
        res = res.json()
        for entity in res["entities"]:
            res_groups.append(entity["status"]["name"])

        return res_groups

    def availability_sets(self, account_id, resource_group):
        Obj = get_resource_api(azure.AVAILABILTY_SETS, self.connection)
        payload = {
            "filter": "account_uuid=={};resource_group=={}".format(
                account_id, resource_group
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        name_id_map = {}
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            entity_uuid = entity["status"]["resources"]["id"]
            name_id_map[name] = entity_uuid

        return name_id_map

    def locations(self, account_id):
        Obj = get_resource_api(azure.LOCATIONS, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        name_value_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["displayName"]
            value = entity["status"]["resources"]["name"]
            name_value_map[name] = value

        return name_value_map

    def hardware_profiles(self, account_id, location):
        Obj = get_resource_api(azure.VM_SIZES, self.connection)
        payload = {
            "filter": "account_uuid=={};location=={}".format(account_id, location)
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        hwprofiles = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            max_disk_count = entity["status"]["resources"]["maxDataDiskCount"]
            hwprofiles[name] = max_disk_count

        return hwprofiles

    def custom_images(self, account_id, location):
        Obj = get_resource_api(azure.SUBSCRIPTION_IMAGES, self.connection)
        payload = {
            "filter": "account_uuid=={};location=={}".format(account_id, location)
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        name_id_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            id = entity["status"]["resources"]["id"]
            name_id_map[name] = id

        return name_id_map

    def image_publishers(self, account_id, location):
        Obj = get_resource_api(azure.IMAGE_PUBLISHERS, self.connection)
        payload = {
            "filter": "account_uuid=={};location=={}".format(account_id, location)
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entity_list = []
        for entity in res["entities"]:
            name = entity["status"]["name"]
            entity_list.append(name)

        return entity_list

    def image_offers(self, account_id, location, publisher):
        Obj = get_resource_api(azure.IMAGE_OFFERS, self.connection)
        payload = {
            "filter": "account_uuid=={};location=={};publisher=={}".format(
                account_id, location, publisher
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entity_list = []
        for entity in res["entities"]:
            name = entity["status"]["name"]
            entity_list.append(name)

        return entity_list

    def image_skus(self, account_id, location, publisher, offer):
        Obj = get_resource_api(azure.IMAGE_SKUS, self.connection)
        payload = {
            "filter": "account_uuid=={};location=={};publisher=={};offer=={}".format(
                account_id, location, publisher, offer
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entity_list = []
        for entity in res["entities"]:
            name = entity["status"]["name"]
            entity_list.append(name)

        return entity_list

    def image_versions(self, account_id, location, publisher, offer, sku):
        Obj = get_resource_api(azure.IMAGE_VERSIONS, self.connection)
        payload = {
            "filter": "account_uuid=={};location=={};publisher=={};offer=={};sku=={}".format(
                account_id, location, publisher, offer, sku
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entity_list = []
        for entity in res["entities"]:
            name = entity["status"]["name"]
            entity_list.append(name)

        return entity_list

    def security_groups(self, account_id, resource_group, location):
        Obj = get_resource_api(azure.SECURITY_GROUPS, self.connection)
        payload = {
            "filter": "account_uuid=={};location=={};resource_group=={}".format(
                account_id, location, resource_group
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entity_list = []
        for entity in res["entities"]:
            name = entity["status"]["name"]
            entity_list.append(name)

        return entity_list

    def virtual_networks(self, account_id, resource_group, location):
        Obj = get_resource_api(azure.VIRTUAL_NETWORKS, self.connection)
        payload = {
            "filter": "account_uuid=={};location=={};resource_group=={}".format(
                account_id, location, resource_group
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entity_list = []
        for entity in res["entities"]:
            name = entity["status"]["name"]
            entity_list.append(name)

        return entity_list

    def subnets(self, account_id, resource_group, virtual_network):
        Obj = get_resource_api(azure.SUBNETS, self.connection)
        payload = {
            "filter": "account_uuid=={};virtual_network=={};resource_group=={}".format(
                account_id, virtual_network, resource_group
            )
        }
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entity_list = []
        for entity in res["entities"]:
            name = entity["status"]["name"]
            entity_list.append(name)

        return entity_list


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def create_spec(client):

    spec = {}
    Obj = Azure(client.connection)

    account_id = ""
    resource_group = ""
    location = ""
    vm_os = ""

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

    payload = {"filter": "type==azure"}
    res, err = client.account.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    azure_accounts = {}

    for entity in res["entities"]:
        entity_name = entity["metadata"]["name"]
        entity_id = entity["metadata"]["uuid"]
        if entity_id in reg_accounts:
            azure_accounts[entity_name] = entity_id

    accounts = list(azure_accounts.keys())
    spec["resources"] = {}

    click.echo("\nChoose from given AZURE accounts")
    for ind, name in enumerate(accounts):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        res = click.prompt("\nEnter the index of account to be used", default=1)
        if (res > len(accounts)) or (res <= 0):
            click.echo("Invalid index !!! ")

        else:
            account_name = accounts[res - 1]
            account_id = azure_accounts[account_name]  # TO BE USED

            spec["resources"]["account_uuid"] = account_id
            click.echo("{} selected".format(highlight_text(account_name)))
            break

    if not account_id:
        click.echo(
            highlight_text("No azure account found registered in this project !!!")
        )
        click.echo("Please add one !!!")
        return

    click.echo("\nChoose from given Operating System types:")
    os_types = azure.OPERATING_SYSTEMS

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

    click.echo("\n\t\t", nl=False)
    click.secho("VM Configuration", bold=True, underline=True)

    vm_name = "vm-@@{calm_unique_hash}@@-@@{calm_array_index}@@"
    spec["resources"]["vm_name"] = click.prompt(
        "\nEnter instance name", default=vm_name
    )

    # Add resource group
    resource_groups = Obj.resource_groups(account_id)
    if not resource_groups:
        click.echo("\n{}".format(highlight_text("No resource group present")))

    else:
        click.echo("\nChoose from given resource groups")
        for ind, name in enumerate(resource_groups):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of resource group", default=1)
            if (res > len(resource_groups)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                resource_group = resource_groups[res - 1]  # TO BE USED
                spec["resources"]["resource_group"] = resource_group
                click.echo("{} selected".format(highlight_text(resource_group)))
                break

    # Add availabililty set
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add a availabilty set")), default="n"
    )
    if choice[0] == "y":
        availability_sets = Obj.availability_sets(account_id, resource_group)
        avl_set_list = list(availability_sets.keys())

        if not avl_set_list:
            click.echo("\n{}".format(highlight_text("No availability_set present")))

        else:
            click.echo("\nChoose from given availabilty set")
            for ind, name in enumerate(avl_set_list):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                res = click.prompt("\nEnter the index of availabilty set", default=1)
                if (res > len(avl_set_list)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    avl_set = avl_set_list[res - 1]
                    spec["resources"]["availability_set_id"] = availability_sets[
                        avl_set
                    ]
                    click.echo("{} selected".format(highlight_text(avl_set)))
                    break

    # Add location
    locations = Obj.locations(account_id)
    if not locations:
        click.echo("\n{}".format(highlight_text("No location group present")))

    else:
        click.echo("\nChoose from given locations")
        location_names = list(locations.keys())
        for ind, name in enumerate(location_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of resource group", default=1)
            if (res > len(location_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                location = location_names[res - 1]
                click.echo("{} selected".format(highlight_text(location)))
                location = locations[location]
                spec["resources"]["location"] = location
                break

    hardware_profiles = Obj.hardware_profiles(account_id, location)
    if not hardware_profiles:
        click.echo("\n{}".format(highlight_text("No hardware profile present")))

    else:
        click.echo("\nChoose from given Hardware Profiles")
        hw_profile_names = list(hardware_profiles.keys())

        for ind, name in enumerate(hw_profile_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of Hardware Profile", default=1)
            if (res > len(hw_profile_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                hw_profile = hw_profile_names[res - 1]
                click.echo("{} selected".format(highlight_text(hw_profile)))
                spec["resources"]["hw_profile"] = {
                    "vm_size": hw_profile,
                    "max_data_disk_count": hardware_profiles[hw_profile],
                }
                break

    # OS Profile
    spec["resources"]["os_profile"] = get_os_profile(vm_os)

    # Storage Profile
    spec["resources"]["storage_profile"] = get_storage_profile(
        Obj, account_id, location
    )

    # Network Profile
    spec["resources"]["nw_profile"] = {}
    spec["resources"]["nw_profile"]["nic_list"] = get_nw_profile(
        Obj, account_id, resource_group, location
    )

    # Add tags
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

    AzureVmProvider.validate_spec(spec)
    click.secho("\nCreate spec for your AZURE VM:\n", underline=True)
    click.echo(highlight_text(yaml.dump(spec, default_flow_style=False)))


def get_os_profile(os_type):

    click.echo("\n\t\t", nl=False)
    click.secho("OS PROFILE DETAILS", bold=True, underline=True)
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add secrets")), default="n"
    )

    res = {}
    res["secrets"] = []
    certificate_list = []
    while choice[0] == "y":
        vault_id = click.prompt("\n\tEnter Vault ID ", default="")
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Add Vault Certificate Details")),
            default="n",
        )

        vault_certificates = []
        while choice[0] == "y":
            certificate_store = ""
            certificate_url = click.prompt("\n\tEnter Certificate URL", default="URL")
            if os_type == "Windows":
                certificate_store = click.prompt(
                    "\n\tEnter Certificate Store", default="Store"
                )

            vault_certificates.append(
                {
                    "certificate_url": certificate_url,
                    "certificate_store": certificate_store,
                }
            )

            if certificate_url:
                certificate_list.append(certificate_url)

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Add more certificates")), default="n"
            )

        res["secrets"].append(
            {"source_vault_id": vault_id, "vault_certificates": vault_certificates}
        )

        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Add more secrets")), default="n"
        )

    if os_type == "Linux":
        res["linux_config"] = get_linux_config()

    else:
        res["windows_config"] = get_windows_config(certificate_list)

    return res


def get_linux_config():

    custom_data = click.prompt("\nEnter Cloud Init Script", default="")
    return {"custom_data": custom_data}


def get_windows_config(certificate_list):

    provision_vm_agent = click.prompt(
        "\n{}(y/n)".format(highlight_text("Enable Provision Windows Guest Agent")),
        default="n",
    )
    provision_vm_agent = True if provision_vm_agent[0] == "y" else False
    auto_updates = click.prompt(
        "\n{}(y/n)".format(highlight_text("Enable Automatic OS Upgrades")), default="n"
    )
    auto_updates = True if auto_updates[0] == "y" else False

    unattend_content = []
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add ADDITIONAL UNATTENDED CONTENT")),
        default="n",
    )
    settings = azure.UNATTENDED_SETTINGS
    while (choice[0] == "y") and settings:
        click.echo("\nChoose from given Setting Names")
        setting = ""
        for ind, name in enumerate(settings):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of Setting", default=1)
            if (res > len(settings)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                setting = settings[res - 1]
                settings.pop(res - 1)
                click.echo("{} selected".format(highlight_text(setting)))
                break

        xml_content = click.prompt(
            "\nEnter XML Content(Please use <{}> as the root element)".format(setting),
            default="",
        )
        unattend_content.append({"setting_name": setting, "xml_content": xml_content})

        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more Unattended content")),
            default="n",
        )

    winrm_listensers = []
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add WINRM LISTENERS")), default="n"
    )
    protocols = list(azure.PROTOCOLS.keys())
    while (choice[0] == "y") and protocols:
        click.echo("\nChoose from given Protocols")
        protocol = ""
        for ind, name in enumerate(protocols):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of protocol", default=1)
            if (res > len(protocols)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                protocol = protocols[res - 1]
                protocols.pop(res - 1)
                click.echo("{} selected".format(highlight_text(protocol)))
                break

        if protocol == "HTTPS":
            cert_url = ""
            click.echo("Choose from given certificate URLs")
            for ind, name in enumerate(certificate_list):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                res = click.prompt("\nEnter the index of certificate URL", default=1)
                if (res > len(certificate_list)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    cert_url = certificate_list[res - 1]
                    click.echo("{} selected".format(highlight_text(cert_url)))
                    break

            winrm_listensers.append(
                {"protocol": azure.PROTOCOLS[protocol], "certificate_url": cert_url}
            )

        else:
            winrm_listensers.append({"protocol": azure.PROTOCOLS[protocol]})

        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more Winrm Listeners")),
            default="n",
        )

    return {
        "winrm_listeners": winrm_listensers,
        "additional_unattend_content": unattend_content,
        "provision_vm_agent": provision_vm_agent,
        "auto_updates": auto_updates,
    }


def get_storage_profile(azure_obj, account_id, location):

    click.echo("\n\t\t", nl=False)
    click.secho("STORAGE PROFILE DETAILS", bold=True, underline=True)

    click.secho("\n1. VM Image Details", underline=True)
    vm_image = {}

    use_custom_image = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to use custom image")), default="n"
    )
    use_custom_image = True if use_custom_image[0] == "y" else False

    if use_custom_image:
        vm_image = get_custom_vm_image(azure_obj, account_id, location)

    else:
        vm_image = get_non_custom_vm_image(azure_obj, account_id, location)

    click.secho("\n2. OS Disk Details", underline=True)
    os_disk = get_os_disk(use_custom_image)

    click.secho("\n3. Data Disk Details", underline=True)
    data_disks = get_data_disks()

    return {
        "is_managed": True,  # Hardcoded in UI
        "os_disk_details": os_disk,
        "data_disk_list": data_disks,
        "image_details": vm_image,
    }


def get_data_disks():

    disks = []

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add data disks")), default="n"
    )

    disk_index = 0
    while choice[0] == "y":
        click.echo("\n\t\t", nl=False)
        click.secho("Data-Disk {}".format(disk_index + 1), underline=True)

        storage_type = ""
        disk_name = "data-disk-@@{calm_unique_hash}@@-@@{calm_array_index}@@-" + str(
            disk_index
        )
        disk_name = click.prompt("\nEnter data disk name", default=disk_name)

        # Add storage type
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add storage type to disk")),
            default="n",
        )
        if choice[0] == "y":
            storage_types = azure.STORAGE_TYPES
            display_names = list(storage_types.keys())
            click.echo("\nChoose from given storage types")
            for ind, name in enumerate(display_names):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                res = click.prompt("\nEnter the index of storage type", default=1)
                if (res > len(display_names)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    storage_type = display_names[res - 1]
                    click.echo("{} selected".format(highlight_text(storage_type)))
                    storage_type = storage_types[storage_type]
                    break

        # Add cache type
        cache_types = azure.CACHE_TYPES
        display_names = list(cache_types.keys())
        click.echo("\nChoose from given cache types")
        for ind, name in enumerate(display_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of cache type", default=1)
            if (res > len(display_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                cache_type = display_names[res - 1]
                click.echo("{} selected".format(highlight_text(cache_type)))
                cache_type = cache_types[cache_type]
                break

        # Add disk size
        disk_size = click.prompt("\nEnter the size for disk(in GiB)", default=1)

        # Add disk lun
        disk_lun = click.prompt("\nEnter the Disk LUN", default=0)

        disks.append(
            {
                "size_in_gb": disk_size,
                "name": disk_name,
                "storage_type": storage_type,
                "caching_type": cache_type,
                "lun": disk_lun,
            }
        )

        disk_index += 1
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more data disks")),
            default="n",
        )

    return disks


def get_os_disk(use_custom_image):

    disk_create_option = ""
    cache_type = ""
    storage_type = ""

    disk_name = "os-@@{calm_unique_hash}@@-@@{calm_array_index}@@-disk"
    disk_name = click.prompt("\nEnter os disk name", default=disk_name)

    # Add storage type
    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add storage type to os disk")),
        default="n",
    )
    if choice[0] == "y":
        storage_types = azure.STORAGE_TYPES
        display_names = list(storage_types.keys())
        click.echo("\nChoose from given storage types")
        for ind, name in enumerate(display_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of storage type", default=1)
            if (res > len(display_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                storage_type = display_names[res - 1]
                click.echo("{} selected".format(highlight_text(storage_type)))
                storage_type = storage_types[storage_type]
                break

    # Add cache type
    cache_types = azure.CACHE_TYPES
    display_names = list(cache_types.keys())
    click.echo("\nChoose from given cache types")
    for ind, name in enumerate(display_names):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        res = click.prompt("\nEnter the index of cache type", default=1)
        if (res > len(display_names)) or (res <= 0):
            click.echo("Invalid index !!! ")

        else:
            cache_type = display_names[res - 1]
            click.echo("{} selected".format(highlight_text(cache_type)))
            cache_type = cache_types[cache_type]
            break

    # Add Disk Create Option
    if use_custom_image:
        disk_create_option = azure.DISK_CREATE_OPTIONS["FROMIMAGE"]
        click.secho(
            "\nNote: In case of custom vm image, Os Disk Create Option : {}".format(
                disk_create_option
            )
        )

    else:
        disk_create_options = azure.DISK_CREATE_OPTIONS
        display_names = list(disk_create_options.keys())
        click.echo("\nChoose from given disk create option")
        for ind, name in enumerate(display_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of disk create option", default=1)
            if (res > len(display_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                disk_create_option = display_names[res - 1]
                click.echo("{} selected".format(highlight_text(disk_create_option)))
                disk_create_option = disk_create_options[disk_create_option]
                break

    return {
        "name": disk_name,
        "storage_type": storage_type,
        "caching_type": cache_type,
        "create_option": disk_create_option,
    }


def get_non_custom_vm_image(azure_obj, account_id, location):

    image_publisher = ""
    image_offer = ""
    image_sku = ""
    image_version = ""

    # Add image publisher
    publishers = azure_obj.image_publishers(account_id, location)
    if not publishers:
        click.echo("\n{}".format(highlight_text("No image publisher present")))

    else:
        click.echo("\nChoose from given image publisher")
        for ind, name in enumerate(publishers):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of image publisher", default=1)
            if (res > len(publishers)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                image_publisher = publishers[res - 1]
                click.echo("{} selected".format(highlight_text(image_publisher)))
                break

    # Add image offer
    image_offers = azure_obj.image_offers(account_id, location, image_publisher)
    if not image_offers:
        click.echo("\n{}".format(highlight_text("No image offer present")))

    else:
        click.echo("\nChoose from given image offer")
        for ind, name in enumerate(image_offers):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of image offer", default=1)
            if (res > len(image_offers)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                image_offer = image_offers[res - 1]
                click.echo("{} selected".format(highlight_text(image_offer)))
                break

    # Add Image SKU
    image_skus = azure_obj.image_skus(
        account_id, location, image_publisher, image_offer
    )
    if not image_skus:
        click.echo("\n{}".format(highlight_text("No image sku present")))

    else:
        click.echo("\nChoose from given image sku")
        for ind, name in enumerate(image_skus):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of image sku", default=1)
            if (res > len(image_skus)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                image_sku = image_skus[res - 1]
                click.echo("{} selected".format(highlight_text(image_sku)))
                break

    # Add Image Version
    image_versions = azure_obj.image_versions(
        account_id, location, image_publisher, image_offer, image_sku
    )
    if not image_versions:
        click.echo("\n{}".format(highlight_text("No image version present")))

    else:
        click.echo("\nChoose from given image version")
        for ind, name in enumerate(image_versions):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of image version", default=1)
            if (res > len(image_versions)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                image_version = image_versions[res - 1]
                click.echo("{} selected".format(highlight_text(image_version)))
                break

    return {
        "sku": image_sku,
        "publisher": image_publisher,
        "offer": image_offer,
        "version": image_version,
        "use_custom_image": False,
    }


def get_custom_vm_image(azure_obj, account_id, location):
    custom_image_id = ""
    custom_images = azure_obj.custom_images(account_id, location)
    custom_image_names = list(custom_images.keys())

    if not custom_image_names:
        click.echo("\n{}".format(highlight_text("No custom image present")))

    else:
        click.echo("\nChoose from given custom images")
        for ind, name in enumerate(custom_image_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of custom image", default=1)
            if (res > len(custom_image_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                custom_image = custom_image_names[res - 1]
                custom_image_id = custom_images[custom_image]
                click.echo("{} selected".format(highlight_text(custom_image)))
                break

    return {"source_image_id": custom_image_id, "use_custom_image": True}


def get_nw_profile(azure_obj, account_id, resource_grp, location):

    click.echo("\n\t\t", nl=False)
    click.secho("NETWORK PROFILE DETAILS", bold=True, underline=True)
    nics = []

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add NICs")), default="n"
    )

    nic_index = 0
    while choice[0] == "y":
        click.echo("\n\t\t", nl=False)
        click.secho("Nic {}".format(nic_index + 1), underline=True)

        nic_name = "nic-@@{calm_unique_hash}@@-@@{calm_array_index}@@-" + str(nic_index)
        nic_name = click.prompt("\nEnter nic name", default=nic_name)

        security_group = ""
        virtual_network = ""
        subnet = ""

        # Add security group
        security_groups = azure_obj.security_groups(account_id, resource_grp, location)
        if not security_groups:
            click.echo("\n{}".format(highlight_text("No security group present")))

        else:
            click.echo("\nChoose from given security groups")
            for ind, name in enumerate(security_groups):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                res = click.prompt("\nEnter the index of security group", default=1)
                if (res > len(security_groups)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    security_group = security_groups[res - 1]
                    click.echo("{} selected".format(highlight_text(security_group)))
                    break

        # Add virtual network
        virtual_networks = azure_obj.virtual_networks(
            account_id, resource_grp, location
        )
        if not virtual_networks:
            click.echo("\n{}".format(highlight_text("No virtual network present")))

        else:
            click.echo("\nChoose from given virtual networtks")
            for ind, name in enumerate(virtual_networks):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                res = click.prompt("\nEnter the index of virtual network", default=1)
                if (res > len(virtual_networks)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    virtual_network = virtual_networks[res - 1]
                    click.echo("{} selected".format(highlight_text(virtual_network)))
                    break

        # Add subnet
        subnets = azure_obj.subnets(account_id, resource_grp, virtual_network)
        if not subnets:
            click.echo("\n{}".format(highlight_text("No subnet present")))

        else:
            click.echo("\nChoose from given subnets")
            for ind, name in enumerate(subnets):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                res = click.prompt("\nEnter the index of subnet", default=1)
                if (res > len(subnets)) or (res <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    subnet = subnets[res - 1]
                    click.echo("{} selected".format(highlight_text(subnet)))
                    break

        click.secho("\nPublic IP Config", underline=True)
        public_ip_info = get_public_ip_info(nic_index)

        click.secho("\nPrivate IP Config", underline=True)
        private_ip_info = get_private_ip_info()

        nics.append(
            {
                "nsg_name": security_group,
                "vnet_name": virtual_network,
                "private_ip_info": private_ip_info,
                "nic_name": nic_name,
                "subnet_name": subnet,
                "public_ip_info": public_ip_info,
            }
        )

        nic_index += 1
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more nics")), default="n"
        )

    return nics


def get_public_ip_info(nic_index=0):

    ip_name = "public-ip-@@{calm_unique_hash}@@-@@{calm_array_index}@@-" + str(
        nic_index
    )
    ip_name = click.prompt("\nEnter public ip name", default=ip_name)

    dns_label = "dns-@@{calm_unique_hash}@@-@@{calm_array_index}@@-" + str(nic_index)
    dns_label = click.prompt("\nEnter DNS Label", default=dns_label)

    allocation_methods = azure.ALLOCATION_METHODS
    click.echo("\nChoose from given ip allocation method")
    for ind, name in enumerate(allocation_methods):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        res = click.prompt("\nEnter the index of allocation methods", default=1)
        if (res > len(allocation_methods)) or (res <= 0):
            click.echo("Invalid index !!! ")

        else:
            allocation_method = allocation_methods[res - 1]
            click.echo("{} selected".format(highlight_text(allocation_method)))
            break

    return {
        "ip_allocation_method": allocation_method,
        "dns_label": dns_label,
        "ip_name": ip_name,
    }


def get_private_ip_info():

    allocation_method = ""
    ip_address = ""

    allocation_methods = azure.ALLOCATION_METHODS
    click.echo("\nChoose from given ip allocation method")
    for ind, name in enumerate(allocation_methods):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        res = click.prompt("\nEnter the index of allocation methods", default=1)
        if (res > len(allocation_methods)) or (res <= 0):
            click.echo("Invalid index !!! ")

        else:
            allocation_method = allocation_methods[res - 1]
            click.echo("{} selected".format(highlight_text(allocation_method)))
            break

    if allocation_method == "Static":
        ip_address = click.prompt("\nEnter IP Address", default="")

    return {"ip_allocation_method": allocation_method, "ip_address": ip_address}
