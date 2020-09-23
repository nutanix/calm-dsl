import click
from ruamel import yaml

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.providers import get_provider_interface
from .constants import VCENTER as vmw


Provider = get_provider_interface()


class VCenterVmProvider(Provider):

    provider_type = "VMWARE_VM"
    package_name = __name__
    spec_template_file = "vmware_vm_provider_spec.yaml.jinja2"

    @classmethod
    def create_spec(cls):
        client = get_api_client()
        create_spec(client)

    @classmethod
    def update_vm_image_config(cls, spec, vm_template=None):
        """vm_template is the downloadable class"""
        if vm_template:
            spec["template"] = vm_template.__name__

    @classmethod
    def get_api_obj(cls):
        """returns object to call vmware provider specific apis"""

        client = get_api_client()
        return VCenter(client.connection)


class VCenter:
    def __init__(self, connection):
        self.connection = connection

    def hosts(self, account_id):
        Obj = get_resource_api(vmw.HOST, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        name_id_map = {}
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            entity_uuid = entity["status"]["resources"]["summary"]["hardware"]["uuid"]
            name_id_map[name] = entity_uuid

        return name_id_map

    def datastores(self, account_id, cluster_name=None, host_id=None):
        Obj = get_resource_api(vmw.DATASTORE, self.connection)
        payload = ""
        if host_id:
            payload = {
                "filter": "account_uuid=={};host_id=={}".format(account_id, host_id)
            }

        if cluster_name:
            payload = {
                "filter": "account_uuid=={};cluster_name=={}".format(
                    account_id, cluster_name
                )
            }

        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        name_url_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            url = entity["status"]["resources"]["summary"]["url"]
            name_url_map[name] = url

        return name_url_map

    def clusters(self, account_id):
        Obj = get_resource_api(vmw.CLUSTER, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}

        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        cluster_list = []
        res = res.json()
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            cluster_list.append(name)

        return cluster_list

    def storage_pods(self, account_id):
        Obj = get_resource_api(vmw.STORAGE_POD, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}

        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        pod_list = []
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            pod_list.append(name)

        return pod_list

    def templates(self, account_id):
        Obj = get_resource_api(vmw.TEMPLATE, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        name_id_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            temp_id = entity["status"]["resources"]["config"]["instanceUuid"]
            name_id_map[name] = temp_id

        return name_id_map

    def customizations(self, account_id, os):

        Obj = get_resource_api(vmw.CUSTOMIZATION, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}

        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        cust_list = []
        for entity in res["entities"]:
            if entity["status"]["resources"]["type"] == os:
                cust_list.append(entity["status"]["resources"]["name"])

        return cust_list

    def timezones(self, os):

        Obj = get_resource_api(vmw.TIMEZONE, self.connection)
        payload = {"filter": "guest_os=={};".format(os)}

        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        name_ind_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            ind = entity["status"]["resources"]["index"]
            name_ind_map[name] = ind

        return name_ind_map

    def networks(self, account_id, host_id=None, cluster_name=None):
        Obj = get_resource_api(vmw.NETWORK, self.connection)
        payload = ""
        if host_id:
            payload = {
                "filter": "account_uuid=={};host_id=={}".format(account_id, host_id)
            }

        if cluster_name:
            payload = {
                "filter": "account_uuid=={};cluster_name=={}".format(
                    account_id, cluster_name
                )
            }

        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        name_id_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            entity_id = entity["status"]["resources"]["id"]

            name_id_map[name] = entity_id

        return name_id_map

    def file_paths(
        self,
        account_id,
        datastore_url=None,
        file_extension="iso",
        host_id=None,
        cluster_name=None,
    ):

        Obj = get_resource_api(vmw.FILE_PATHS, self.connection)
        payload = ""
        if datastore_url:
            payload = {
                "filter": "account_uuid=={};file_extension=={};datastore_url=={}".format(
                    account_id, file_extension, datastore_url
                )
            }
        elif host_id:
            payload = {
                "filter": "account_uuid=={};file_extension=={};host_id=={}".format(
                    account_id, file_extension, host_id
                )
            }
        else:
            payload = {
                "filter": "account_uuid=={};file_extension=={};cluster_name=={}".format(
                    account_id, file_extension, cluster_name
                )
            }

        res, err = Obj.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        fpaths = []
        for entity in res["entities"]:
            fpaths.append(entity["status"]["resources"])

        return fpaths

    def template_defaults(self, account_id, template_id):  # TODO improve this mess
        payload = {"filter": 'template_uuids==["{}"];'.format(template_id)}
        Obj = get_resource_api(vmw.TEMPLATE_DEFS.format(account_id), self.connection)
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        tempControllers = {}
        tempDisks = []
        tempNics = []
        free_device_slots = {}
        controller_count = {"SCSI": 0, "SATA": 0, "IDE": 0}
        controller_key_type_map = {
            1000: ("SCSI", None),
            15000: ("SATA", None),
            200: ("IDE", None),
        }
        controller_label_key_map = {"SCSI": {}, "SATA": {}, "IDE": {}}

        controllers = []
        disks = []
        networks = []

        for entity in res["entities"]:
            entity_config = entity["status"]["resources"]["config"]
            entity_id = entity_config["instanceUuid"]
            if entity_id == template_id:
                controllers = entity_config["hardware"]["device"]["controller"] or []
                disks = entity_config["hardware"]["device"]["disk"] or []
                networks = entity_config["hardware"]["device"]["network"] or []
                break

        for controller in controllers:
            contlr = {}

            label = controller["label"]
            free_device_slots[label] = controller["freeDeviceSlots"]
            type = controller["type"]
            if vmw.ControllerMap.get(type):
                controller_type = vmw.ControllerMap[type]
            else:
                controller_type = "IDE"  # SCSI/SATA/IDE

            ctlr_type = vmw.VirtualControllerNameMap[type]

            if controller_type == "SCSI":
                contlr["controller_type"] = vmw.SCSIControllerOptions[ctlr_type]

            elif controller_type == "SATA":
                contlr["controller_type"] = vmw.SATAControllerOptions[ctlr_type]

            contlr["key"] = controller["key"]
            controller_label_key_map[controller_type][label] = contlr["key"]
            controller_key_type_map[contlr["key"]] = (controller_type, label)

            controller_count[controller_type] += 1
            if controller_type == "SCSI":
                contlr["bus_sharing"] = controller["sharedBus"]

            if not tempControllers.get(controller_type):
                tempControllers[controller_type] = []

            tempControllers[controller_type].append(contlr)

        disk_mode_inv = {v: k for k, v in vmw.DISK_MODE.items()}
        for disk in disks:
            dsk = {}

            dsk["disk_type"] = vmw.DiskMap[disk["type"]]
            dsk["key"] = disk["key"]
            dsk["controller_key"] = disk["controllerKey"]

            if controller_key_type_map.get(disk["controllerKey"]):
                dsk["adapter_type"] = controller_key_type_map.get(
                    disk["controllerKey"]
                )[0]
            else:
                dsk["adapter_type"] = "IDE"  # Taken from VMwareTemplateDisks.jsx

            if dsk["disk_type"] == "disk":
                dsk["size"] = disk["capacityInKB"] // 1024
                dsk["mode"] = disk_mode_inv[disk["backing"]["diskMode"]]
                dsk["location"] = (
                    disk["backing"]["datastore"]["url"],
                    disk["backing"]["datastore"]["name"],
                )
                dsk["device_slot"] = disk["unitNumber"]

            tempDisks.append(dsk)

        for network in networks:
            nic = {}
            nic["key"] = network["key"]
            nic["net_name"] = network["backing"]["network"]["name"]
            nic["nic_type"] = vmw.NetworkAdapterMap.get(network["type"], "")

            tempNics.append(nic)

        response = {
            "tempControllers": tempControllers,
            "tempDisks": tempDisks,
            "tempNics": tempNics,
            "free_device_slots": free_device_slots,
            "controller_count": controller_count,
            "controller_key_type_map": controller_key_type_map,
            "controller_label_key_map": controller_label_key_map,
        }

        return response


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def create_spec(client):

    spec = {}
    Obj = VCenter(client.connection)

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

    payload = {"filter": "type==vmware"}
    res, err = client.account.list(payload)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    vmware_accounts = []

    for entity in res["entities"]:
        vmware_accounts.append(entity["metadata"]["uuid"])

    account_id = ""
    for account in accounts:
        if account["uuid"] in vmware_accounts:
            account_id = account["uuid"]
            break

    if not account_id:
        click.echo(
            highlight_text("No vmware account found registered in this project !!!")
        )
        click.echo("Please add one !!!")
        return

    click.echo("\nChoose from given Operating System types:")
    os_types = list(vmw.OperatingSystem.keys())
    for ind, name in enumerate(os_types):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        ind = click.prompt("\nEnter the index of operating system", default=1)
        if (ind > len(os_types)) or (ind <= 0):
            click.echo("Invalid index !!! ")

        else:
            os = os_types[ind - 1]
            click.echo("{} selected".format(highlight_text(os)))
            break

    drs_mode = click.prompt("\nEnable DRS Mode(y/n)", default="n")
    drs_mode = True if drs_mode[0] == "y" else False
    spec["drs_mode"] = drs_mode

    if not drs_mode:
        host_name_id_map = Obj.hosts(account_id)
        host_names = list(host_name_id_map.keys())
        if not host_names:
            click.echo("\n{}".format(highlight_text("No hosts present")))

        else:
            click.echo("\nChoose from given hosts:")
            for ind, name in enumerate(host_names):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of host", default=1)
                if (ind > len(host_names)) or (ind <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    host_name = host_names[ind - 1]
                    host_id = host_name_id_map[host_name]  # TO BE USED
                    spec["host"] = host_id
                    click.echo("{} selected".format(highlight_text(host_name)))
                    break

        datastore_name_url_map = Obj.datastores(account_id, host_id=host_id)
        datastore_names = list(datastore_name_url_map.keys())
        if not datastore_names:
            click.echo("\n{}".format(highlight_text("No datastore present")))

        else:
            click.echo("\nChoose from given datastore:")
            for ind, name in enumerate(datastore_names):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of datastore", default=1)
                if (ind > len(datastore_names)) or (ind <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    datastore_name = datastore_names[ind - 1]
                    datastore_url = datastore_name_url_map[datastore_name]  # TO BE USED
                    spec["datastore"] = datastore_url
                    click.echo("{} selected".format(highlight_text(datastore_name)))
                    break

    else:
        cluster_list = Obj.clusters(account_id)
        if not cluster_list:
            click.echo("\n{}".format(highlight_text("No cluster present")))

        else:
            click.echo("\nChoose from given cluster:")
            for ind, name in enumerate(cluster_list):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of cluster", default=1)
                if (ind > len(cluster_list)) or (ind <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    cluster_name = cluster_list[ind - 1]  # TO BE USED
                    spec["cluster"] = cluster_name
                    click.echo("{} selected".format(highlight_text(cluster_name)))
                    break

        storage_pod_list = Obj.storage_pods(account_id)
        if not storage_pod_list:
            click.echo("\n{}".format(highlight_text("No storage pod present")))

        else:
            click.echo("\nChoose from given storage pod:")
            for ind, name in enumerate(storage_pod_list):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of storage", default=1)
                if (ind > len(storage_pod_list)) or (ind <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    pod_name = storage_pod_list[ind - 1]  # TO BE USED
                    spec["storage_pod"] = pod_name
                    click.echo("{} selected".format(highlight_text(pod_name)))
                    break

    template_name_id_map = Obj.templates(account_id)
    template_names = list(template_name_id_map.keys())
    if not template_names:
        click.echo("\n{}".format(highlight_text("No templates present")))

    else:
        click.echo("\nChoose from given templates:")
        for ind, name in enumerate(template_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of template", default=1)
            if (ind > len(template_names)) or (ind <= 0):
                click.echo("Invalid index !!! ")

            else:
                template_name = template_names[ind - 1]
                template_id = template_name_id_map[template_name]  # TO BE USED
                spec["template"] = template_id
                click.echo("{} selected".format(highlight_text(template_name)))
                break

    # VM Configuration
    vm_name = "vm-@@{calm_unique_hash}@@-@@{calm_array_index}@@"
    spec["name"] = click.prompt("\nEnter instance name", default=vm_name)

    spec["resources"] = {}
    spec["resources"]["num_sockets"] = click.prompt("\nEnter no. of vCPUs", default=1)

    spec["resources"]["num_vcpus_per_socket"] = click.prompt(
        "\nCores per vCPU", default=1
    )

    spec["resources"]["memory_size_mib"] = (
        click.prompt("\nMemory(in GiB)", default=1)
    ) * 1024

    response = Obj.template_defaults(account_id, template_id)

    tempControllers = response.get("tempControllers", {})
    tempDisks = response.get("tempDisks", [])
    tempNics = response.get("tempNics", [])
    free_device_slots = response.get("free_device_slots", {})
    controller_count = response.get("controller_count", {})
    controller_key_type_map = response.get("controller_key_type_map", {})
    controller_label_key_map = response.get("controller_label_key_map", {})

    tempSCSIContrlr = tempControllers.get("SCSI", [])
    tempSATAContrlr = tempControllers.get("SATA", [])
    spec["resources"]["template_controller_list"] = []
    spec["resources"]["template_disk_list"] = []
    spec["resources"]["template_nic_list"] = []
    spec["resources"]["controller_list"] = []
    spec["resources"]["disk_list"] = []
    spec["resources"]["nic_list"] = []
    bus_sharing_inv_map = {v: k for k, v in vmw.BUS_SHARING.items()}

    if tempSATAContrlr or tempSCSIContrlr:
        click.secho("\nConfig of Template Controllers:", underline=True)
    else:
        click.echo("\nNo template controllers found!!")

    if tempSCSIContrlr:
        click.secho("\nSCSI Controllers", bold=True, underline=True)

        for index, cntlr in enumerate(tempSCSIContrlr):
            click.echo("\n\t\t", nl=False)
            click.secho("SCSI CONTROLLER {}\n".format(index + 1), underline=True)

            click.echo(
                "\nController Type: {}".format(highlight_text(cntlr["controller_type"]))
            )
            bus_sharing = bus_sharing_inv_map[cntlr["bus_sharing"]]
            click.echo("Bus Sharing: {}".format(highlight_text(bus_sharing)))

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to edit this controller")),
                default="n",
            )
            if choice[0] == "y":
                controllers = list(vmw.CONTROLLER["SCSI"].keys())
                click.echo("\nChoose from given controller types:")
                for ind, name in enumerate(controllers):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt(
                        "\nEnter the index of controller type", default=1
                    )
                    if (ind > len(controllers)) or (ind <= 0):
                        click.echo("Invalid index !!! ")

                    else:
                        controller_type = controllers[ind - 1]
                        click.echo(
                            "{} selected".format(highlight_text(controller_type))
                        )
                        controller_type = vmw.CONTROLLER["SCSI"][controller_type]
                        break

                sharingOptions = list(vmw.BUS_SHARING.keys())
                click.echo("\nChoose from given sharing types:")
                for ind, name in enumerate(sharingOptions):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt("\nEnter the index of sharing type", default=1)
                    if (ind > len(sharingOptions)) or (ind <= 0):
                        click.echo("Invalid index !!! ")

                    else:
                        res = sharingOptions[ind - 1]
                        click.echo("{} selected".format(highlight_text(res)))
                        busSharing = vmw.BUS_SHARING[res]
                        break

                controller = {
                    "controller_type": controller_type,
                    "bus_sharing": busSharing,
                    "is_deleted": False,
                    "key": cntlr["key"],
                }
                spec["resources"]["template_controller_list"].append(controller)

    if tempSATAContrlr:
        click.secho("\nSATA Controllers", bold=True, underline=True)

        for index, cntlr in enumerate(tempSATAContrlr):
            click.echo("\n\t\t", nl=False)
            click.secho("SATA CONTROLLER {}\n".format(index + 1), underline=True)

            click.echo(
                "\nController Type: {}".format(highlight_text(cntlr["controller_type"]))
            )

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to edit this controller")),
                default="n",
            )
            if choice[0] == "y":
                controllers = list(vmw.CONTROLLER["SATA"].keys())
                click.echo("\nChoose from given controller types:")
                for ind, name in enumerate(controllers):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt(
                        "\nEnter the index of controller type", default=1
                    )
                    if (ind > len(controllers)) or (ind <= 0):
                        click.echo("Invalid index !!! ")

                    else:
                        controller_type = controllers[ind - 1]
                        click.echo(
                            "{} selected".format(highlight_text(controller_type))
                        )
                        controller_type = vmw.CONTROLLER["SATA"][controller_type]
                        break

                controller = {
                    "controller_type": controller_type,
                    "is_deleted": False,
                    "key": cntlr["key"],
                }
                spec["resources"]["template_controller_list"].append(controller)

    if tempDisks:
        click.secho("\nConfig of Template Disks:", underline=True)
    else:
        click.echo("\nNo template disks found !!!")

    for index, disk in enumerate(tempDisks):
        click.echo("\n\t\t", nl=False)
        click.secho("vDisk {}\n".format(index + 1), underline=True)
        disk_type = disk["disk_type"]
        adapter_type = disk["adapter_type"]

        click.echo("\nDevice Type: {}".format(highlight_text(disk_type)))
        click.echo("Adapter Type: {}".format(highlight_text(adapter_type)))

        if disk_type == "disk":
            click.echo("Size (in GiB): {}".format(highlight_text(disk["size"] // 1024)))
            click.echo("Location : {}".format(highlight_text(disk["location"][1])))
            controller_label = controller_key_type_map[disk["controller_key"]][1]
            click.echo("Controller: {}".format(highlight_text(controller_label)))
            click.echo("Device Slot: {}".format(highlight_text(disk["device_slot"])))
            click.echo("Disk Mode: {}".format(highlight_text(disk["mode"])))
            click.echo("Exclude from vm config: {}".format(highlight_text("No")))

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to edit this disk")),
                default="n",
            )

            # Only size, disk_mode and excluding checkbox is editable(FROM CALM_UI repo)
            if choice[0] == "y":
                size = click.prompt("\nEnter disk size (in GiB)", default=8)
                click.echo("\nChoose from given disk modes:")

                disk_mode_list = list(vmw.DISK_MODE.keys())
                for ind, name in enumerate(disk_mode_list):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt("\nEnter the index of disk mode", default=1)
                    if (ind > len(disk_mode_list)) or (ind <= 0):
                        click.echo("Invalid index !!! ")

                    else:
                        disk_mode = disk_mode_list[ind - 1]
                        click.echo("{} selected".format(highlight_text(disk_mode)))
                        disk_mode = vmw.DISK_MODE[disk_mode]
                        break

                is_deleted = click.prompt(
                    "\n{}(y/n)".format(highlight_text("Exclude disk from vm config")),
                    default="n",
                )
                is_deleted = True if is_deleted[0] == "y" else False
                dsk = {
                    "disk_size_mb": size * 1024,
                    "is_deleted": is_deleted,
                    "disk_mode": disk_mode,
                    "adapter_type": adapter_type,
                    "disk_type": disk_type,
                    "key": disk["key"],
                    "controller_key": disk["controller_key"],
                    "device_slot": disk["device_slot"],
                    "location": disk["location"][0],
                }

                spec["resources"]["template_disk_list"].append(dsk)
        else:
            click.echo(highlight_text("\nNo field can be edited in this template disk"))

    if tempNics:
        click.secho("\nConfig of Template Network Adapters:", underline=True)
    else:
        click.echo("\nNo template network adapters found !!!")

    for index, nic in enumerate(tempNics):
        click.echo("\n\t\t", nl=False)
        click.secho("vNIC-{}\n".format(index + 1), underline=True)
        click.echo("\nAdapter Type: {}".format(highlight_text(nic["nic_type"])))
        click.echo("Network Type: {}".format(highlight_text(nic["net_name"])))
        click.echo("Exclude from vm config: {}".format(highlight_text("No")))

        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to edit this nic")), default="n"
        )
        if choice[0] == "y":
            click.echo("\nChoose from given network adapters:")
            adapter_types = list(vmw.NetworkAdapterMap.values())
            for ind, name in enumerate(adapter_types):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of adapter type", default=1)
                if (ind > len(adapter_types)) or (ind <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    adapter_type = adapter_types[ind - 1]
                    click.echo("{} selected".format(highlight_text(adapter_type)))
                    break

            if not drs_mode:
                network_name_id_map = Obj.networks(account_id, host_id=host_id)
            else:
                network_name_id_map = Obj.networks(
                    account_id, cluster_name=cluster_name
                )

            click.echo("\nChoose from given network types:")
            network_names = list(network_name_id_map.keys())
            for ind, name in enumerate(network_names):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of network type", default=1)
                if (ind > len(network_names)) or (ind <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    network_name = network_names[ind - 1]
                    click.echo("{} selected".format(highlight_text(network_name)))
                    network_id = network_name_id_map[network_name]
                    break

            is_deleted = click.prompt(
                "\n{}(y/n)".format(highlight_text("Exclude network from vm config")),
                default="n",
            )
            is_deleted = True if is_deleted[0] == "y" else False

            network = {
                "nic_type": adapter_type,
                "is_deleted": is_deleted,
                "net_name": network_id,
                "key": nic["key"],
            }

            spec["resources"]["template_nic_list"].append(network)

    click.secho("\nControllers", underline=True)

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add SCSI controllers")), default="n"
    )
    while choice[0] == "y":
        if controller_count["SCSI"] == vmw.ControllerLimit["SCSI"]:
            click.echo(highlight_text("\nNo more SCSI controller can be added"))

        label = "SCSI controller {}".format(controller_count["SCSI"])
        key = controller_count["SCSI"] + vmw.KEY_BASE["CONTROLLER"]["SCSI"]
        controller_label_key_map["SCSI"][label] = key

        click.echo("\n\t\t", nl=False)
        click.secho("{}\n".format(label), underline=True)

        controllers = list(vmw.CONTROLLER["SCSI"].keys())
        click.echo("\nChoose from given controller types:")
        for ind, name in enumerate(controllers):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of controller type", default=1)
            if (ind > len(controllers)) or (ind <= 0):
                click.echo("Invalid index !!!")

            else:
                controller_type = controllers[ind - 1]
                click.echo("{} selected".format(highlight_text(controller_type)))
                controller_type = vmw.CONTROLLER["SCSI"][controller_type]
                break

        free_device_slots[label] = generate_free_slots(
            vmw.ControllerDeviceSlotMap[controller_type]
        )
        sharingOptions = list(vmw.BUS_SHARING.keys())
        click.echo("\nChoose from given sharing types:")
        for ind, name in enumerate(sharingOptions):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of sharing type", default=1)
            if (ind > len(sharingOptions)) or (ind <= 0):
                click.echo("Invalid index !!! ")

            else:
                res = sharingOptions[ind - 1]
                click.echo("{} selected".format(highlight_text(res)))
                busSharing = vmw.BUS_SHARING[res]
                break

        controller_count["SCSI"] += 1
        controller = {
            "controller_type": controller_type,
            "bus_sharing": busSharing,
            "key": key,
        }

        controller_key_type_map[key] = ("SCSI", label)
        spec["resources"]["controller_list"].append(controller)
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more SCSI controllers")),
            default="n",
        )

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add SATA controllers")), default="n"
    )
    while choice[0] == "y":
        if controller_count["SATA"] == vmw.ControllerLimit["SATA"]:
            click.echo(highlight_text("\nNo more SATA controller can be added"))

        label = "SATA controller {}".format(controller_count["SATA"])
        key = controller_count["SATA"] + vmw.KEY_BASE["CONTROLLER"]["SATA"]
        controller_label_key_map["SATA"][label] = key

        click.echo("\n\t\t", nl=False)
        click.secho("{}\n".format(label), underline=True)

        controllers = list(vmw.CONTROLLER["SATA"].keys())
        click.echo("\nChoose from given controller types:")
        for ind, name in enumerate(controllers):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of controller type", default=1)
            if (ind > len(controllers)) or (ind <= 0):
                click.echo("Invalid index !!! ")

            else:
                controller_type = controllers[ind - 1]
                click.echo("{} selected".format(highlight_text(controller_type)))
                controller_type = vmw.CONTROLLER["SATA"][controller_type]
                break

        free_device_slots[label] = generate_free_slots(
            vmw.ControllerDeviceSlotMap[controller_type]
        )
        controller_count["SATA"] += 1
        controller = {"controller_type": controller_type, "key": key}

        controller_key_type_map[key] = ("SATA", label)
        spec["resources"]["controller_list"].append(controller)
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more SATA controllers")),
            default="n",
        )

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add disks")), default="n"
    )
    while choice[0] == "y":
        click.echo("\nChoose from given disk types:")
        disk_types = list(vmw.DISK_TYPES.keys())
        for ind, name in enumerate(disk_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of disk type", default=1)
            if (ind > len(disk_types)) or (ind <= 0):
                click.echo("Invalid index !!! ")

            else:
                disk_type = disk_types[ind - 1]
                click.echo("{} selected".format(highlight_text(disk_type)))
                disk_type = vmw.DISK_TYPES[disk_type]  # TO BE USED
                break

        click.echo("\nChoose from given adapter types:")
        disk_adapters = vmw.DISK_ADAPTERS[disk_type]
        for ind, name in enumerate(disk_adapters):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of adapter type", default=1)
            if (ind > len(disk_adapters)) or (ind <= 0):
                click.echo("Invalid index !!! ")

            else:
                adapter_type = disk_adapters[ind - 1]
                click.echo("{} selected".format(highlight_text(adapter_type)))
                adapter_type = vmw.DISK_ADAPTER_TYPES[adapter_type]  # TO BE USED
                break

        if disk_type == "disk":
            disk_size = click.prompt("\nEnter disk size (in GiB)", default=8)

            if not drs_mode:
                datastore_name_url_map = Obj.datastores(account_id, host_id=host_id)
            else:
                datastore_name_url_map = Obj.datastores(
                    account_id, cluster_name=cluster_name
                )

            locations = list(datastore_name_url_map.keys())
            click.echo("\nChoose from given locations:")
            for ind, name in enumerate(locations):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of datastore", default=1)
                if ind > len(locations):
                    click.echo("Invalid index !!! ")

                else:
                    datastore_name = locations[ind - 1]
                    click.echo("{} selected".format(highlight_text(datastore_name)))
                    datastore_url = datastore_name_url_map[datastore_name]  # TO BE USED
                    break

            controllers = list(controller_label_key_map[adapter_type].keys())
            if controllers:
                click.echo("\nChoose from given controllers:")
                for ind, name in enumerate(controllers):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt("\nEnter the index of controller", default=1)
                    if ind > len(controllers):
                        click.echo("Invalid index !!! ")

                    else:
                        controller_label = controllers[ind - 1]  # TO BE USED
                        click.echo(
                            "{} selected".format(highlight_text(controller_label))
                        )
                        controller_key = controller_label_key_map[adapter_type][
                            controller_label
                        ]  # TO BE USED
                        break

            click.echo("\nChoose from given device slots:")
            slots = free_device_slots[controller_label]
            for ind, name in enumerate(slots):
                click.echo("\t {}. [ {} ]".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of slots", default=1)
                if ind > len(slots):
                    click.echo("Invalid index !!! ")

                else:
                    device_slot = slots[ind - 1]  # TO BE USED
                    click.echo("{} selected".format(highlight_text(device_slot)))
                    free_device_slots[controller_label].pop(ind - 1)
                    break

            click.echo("\nChoose from given device modes:")
            disk_modes = list(vmw.DISK_MODE.keys())
            for ind, name in enumerate(disk_modes):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of device mode", default=1)
                if ind > len(disk_modes):
                    click.echo("Invalid index !!! ")

                else:
                    disk_mode = disk_modes[ind - 1]  # TO BE USED
                    click.echo("{} selected".format(highlight_text(disk_mode)))
                    disk_mode = vmw.DISK_MODE[disk_mode]
                    break

            dsk = {
                "disk_size_mb": disk_size * 1024,
                "disk_mode": disk_mode,
                "device_slot": device_slot,  # It differs from the request_payload from the UI
                "adapter_type": adapter_type,
                "location": datastore_url,
                "controller_key": controller_key,
                "disk_type": disk_type,
            }

        else:
            click.echo(
                highlight_text(
                    "\nBy default, ISO images across all datastores are available for selection. To filter this list, select a datastore."
                )
            )
            datastore_url = ""

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to add datastore")), default="n"
            )
            if choice[0] == "y":
                if not drs_mode:
                    datastore_name_url_map = Obj.datastores(account_id, host_id=host_id)
                else:
                    datastore_name_url_map = Obj.datastores(
                        account_id, cluster_name=cluster_name
                    )

                datastores = list(datastore_name_url_map.keys())
                click.echo("\nChoose from given datastore:")
                for ind, name in enumerate(datastores):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt("\nEnter the index of datastore", default=1)
                    if (ind > len(datastores)) or (ind <= 0):
                        click.echo("Invalid index !!! ")

                    else:
                        datastore_name = datastores[ind - 1]
                        click.echo("{} selected".format(highlight_text(datastore_name)))
                        datastore_url = datastore_name_url_map[
                            datastore_name
                        ]  # TO BE USED
                        break

            if datastore_url:
                file_paths = Obj.file_paths(account_id, datastore_url=datastore_url)
            elif not drs_mode:
                file_paths = Obj.file_paths(account_id, host_id=host_id)
            else:
                file_paths = Obj.file_paths(account_id, cluster_name=cluster_name)

            click.echo("\nChoose from given ISO file paths:")
            for ind, name in enumerate(file_paths):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of file path", default=1)
                if (ind > len(file_paths)) or (ind <= 0):
                    click.echo("Invalid index !!! ")

                else:
                    iso_file_path = file_paths[ind - 1]
                    click.echo("{} selected".format(highlight_text(iso_file_path)))
                    break

            dsk = {
                "adapter_type": adapter_type,
                "iso_path": iso_file_path,
                "location": datastore_url,
                "disk_type": disk_type,
            }

        spec["resources"]["disk_list"].append(dsk)
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more disks")), default="n"
        )

    click.secho("\nNETWORK ADAPTERS", underline=True)
    click.echo(
        highlight_text(
            "Network Configuration is needed for Actions and Runbooks to work"
        )
    )

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want to add nics")), default="n"
    )
    while choice[0] == "y":
        click.echo("\nChoose from given network adapters:")
        adapter_types = list(vmw.NetworkAdapterMap.values())
        for ind, name in enumerate(adapter_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of adapter type", default=1)
            if (ind > len(adapter_types)) or (ind <= 0):
                click.echo("Invalid index !!! ")

            else:
                adapter_type = adapter_types[ind - 1]
                click.echo("{} selected".format(highlight_text(adapter_type)))
                break

        if not drs_mode:
            network_name_id_map = Obj.networks(account_id, host_id=host_id)
        else:
            network_name_id_map = Obj.networks(account_id, cluster_name=cluster_name)

        click.echo("\nChoose from given network types:")
        network_names = list(network_name_id_map.keys())
        for ind, name in enumerate(network_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of network type", default=1)
            if ind > len(network_names):
                click.echo("Invalid index !!! ")

            else:
                network_name = network_names[ind - 1]
                click.echo("{} selected".format(highlight_text(network_name)))
                network_id = network_name_id_map[network_name]
                break

        network = {"nic_type": adapter_type, "net_name": network_id}
        spec["resources"]["nic_list"].append(network)
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add more nics")), default="n"
        )

    click.secho("\nVM Guest Customization", underline=True)

    gc_enable = click.prompt("\nEnable Guest Customization(y/n)", default="n")
    if gc_enable[0] == "y":
        spec["resources"]["guest_customization"] = _guest_customization(
            Obj, os, account_id
        )
    else:
        spec["resources"]["guest_customization"] = {
            "customization_type": vmw.OperatingSystem[os]
        }

    VCenterVmProvider.validate_spec(spec)
    click.secho("\nCreate spec for your VMW VM:\n", underline=True)
    click.echo(highlight_text(yaml.dump(spec, default_flow_style=False)))


def _windows_customization(Obj, account_id):

    spec = {"customization_type": vmw.OperatingSystem["Windows"], "windows_data": {}}

    click.echo("\nChoose from given Guest Customization Modes:")
    gc_modes = vmw.GuestCustomizationModes["Windows"]

    for ind, name in enumerate(gc_modes):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        res = click.prompt("\nEnter the index of Guest Customization Mode", default=1)
        if (res > len(gc_modes)) or (res <= 0):
            click.echo("Invalid index !!!")

        else:
            gc_mode = gc_modes[res - 1]
            click.echo("{} selected".format(highlight_text(gc_mode)))
            break

    if gc_mode == "Predefined Customization":
        customizations = Obj.customizations(account_id, "Windows")

        if not customizations:
            click.echo(
                highlight_text("No Predefined Guest Customization registered !!!")
            )
            return {}

        click.echo("\nChoose from given customization names:")
        for ind, name in enumerate(customizations):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of Customization Name", default=1)
            if (res > len(customizations)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                custn_name = customizations[res - 1]
                click.echo("{} selected".format(highlight_text(custn_name)))
                break

        return {
            "customization_type": vmw.OperatingSystem["Linux"],
            "customization_name": custn_name,
        }

    else:
        computer_name = click.prompt("\tComputer Name: ", default="")
        full_name = click.prompt("\tFull name: ", default="")
        organization_name = click.prompt("\tOrganization Name: ", default="")
        product_id = click.prompt("\tProduct Id: ", default="")

        timezone_name_ind_map = Obj.timezones(vmw.OperatingSystem["Windows"])
        timezone_names = list(timezone_name_ind_map.keys())
        timezone = ""

        click.echo("\nChoose from given timezone names:")
        for ind, name in enumerate(timezone_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of Timezone", default=1)
            if (res > len(timezone_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                timezone = timezone_names[res - 1]
                click.echo("{} selected".format(highlight_text(timezone)))
                timezone = timezone_name_ind_map[timezone]
                break

        admin_password = click.prompt(
            "\nAdmin Password", default="Admin_password", hide_input=True
        )

        choice = click.prompt(
            "\nAutomatically logon as administrator(y/n)", default="n"
        )
        auto_logon = True if choice[0] == "y" else False

        spec["windows_data"].update(
            {
                "product_id": product_id,
                "computer_name": computer_name,
                "auto_logon": auto_logon,
                "organization_name": organization_name,
                "timezone": timezone,
                "full_name": full_name,
                "password": {
                    "value": admin_password,
                    "attrs": {"is_secret_modified": True},
                },
            }
        )

        if auto_logon:
            login_count = click.prompt(
                "Number of times to logon automatically", default=1
            )
            spec["windows_data"]["login_count"] = login_count

        command_list = []
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add commands")), default="n"
        )

        while choice[0] == "y":
            command = click.prompt("\tCommand", default="")
            command_list.append(command)
            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to add more commands")),
                default="n",
            )

        spec["windows_data"]["command_list"] = command_list

        # Domain and Workgroup Setting
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to join domain")), default="n"
        )
        is_domain = True if choice[0] == "y" else False

        if not is_domain:
            workgroup = click.prompt("\n\tWorkgroup: ", default="")
            spec["windows_data"].update(
                {"is_domain": is_domain, "workgroup": workgroup}
            )

        else:
            domain = click.prompt("\tDomain Name: ", default="")
            domain_user = click.prompt("\tUsername: ", default="admin")
            domain_password = click.prompt(
                "\tPassword: ", default="Domain_password", hide_input=True
            )
            spec["windows_data"].update(
                {
                    "is_domain": is_domain,
                    "domain": domain,
                    "domain_user": domain_user,
                    "domain_password": {
                        "value": domain_password,
                        "attrs": {"is_secret_modified": True},
                    },
                }
            )

    return spec


def _linux_customization(Obj, account_id):

    click.echo("\nChoose from given Guest Customization Modes:")
    gc_modes = vmw.GuestCustomizationModes["Linux"]

    for ind, name in enumerate(gc_modes):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    while True:
        res = click.prompt("\nEnter the index of Guest Customization Mode", default=1)
        if (res > len(gc_modes)) or (res <= 0):
            click.echo("Invalid index !!!")

        else:
            gc_mode = gc_modes[res - 1]
            click.echo("{} selected".format(highlight_text(gc_mode)))
            break

    if gc_mode == "Predefined Customization":
        customizations = Obj.customizations(account_id, "Linux")

        if not customizations:
            click.echo(
                highlight_text("No Predefined Guest Customization registered !!!")
            )
            return {}

        click.echo("\nChoose from given customization names:")
        for ind, name in enumerate(customizations):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of Customization Name", default=1)
            if (res > len(customizations)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                custn_name = customizations[res - 1]
                click.echo("{} selected".format(highlight_text(custn_name)))
                break

        return {
            "customization_type": vmw.OperatingSystem["Linux"],
            "customization_name": custn_name,
        }

    elif gc_mode == "Cloud Init":
        script = click.prompt("\nEnter script", default="")
        return {
            "customization_type": vmw.OperatingSystem["Linux"],
            "cloud_init": script,
        }

    else:
        host_name = click.prompt("\nEnter Hostname", default="")
        domain = click.prompt("\nEnter Domain", default="")

        timezone_name_ind_map = Obj.timezones(vmw.OperatingSystem["Linux"])
        timezone_names = list(timezone_name_ind_map.keys())
        timezone = ""

        click.echo("\nChoose from given timezone names:")
        for ind, name in enumerate(timezone_names):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            res = click.prompt("\nEnter the index of Timezone", default=1)
            if (res > len(timezone_names)) or (res <= 0):
                click.echo("Invalid index !!! ")

            else:
                timezone = timezone_names[res - 1]
                click.echo("{} selected".format(highlight_text(timezone)))
                timezone = timezone_name_ind_map[timezone]
                break

        choice = click.prompt("\nEnable Hardware clock UTC(y/n)", default="n")
        hw_ctc_clock = True if choice[0] == "y" else False

        return {
            "customization_type": vmw.OperatingSystem["Linux"],
            "linux_data": {
                "hw_utc_clock": hw_ctc_clock,
                "domain": domain,
                "hostname": host_name,
                "timezone": timezone,
            },
        }


def _guest_customization(Obj, os, account_id):

    if os == "Windows":
        gc = _windows_customization(Obj, account_id)
        data = "windows_data"

    else:
        gc = _linux_customization(Obj, account_id)
        data = "linux_data"

    if gc.get(data):

        click.secho("\nNetwork Settings", underline=True)
        choice = click.prompt(
            "\n{}(y/n)".format(highlight_text("Want to add a network")), default="n"
        )

        network_settings = []
        while choice[0] == "y":
            choice = click.prompt("\n\tUse DHCP(y/n)", default="y")
            is_dhcp = True if choice[0] == "y" else False

            if not is_dhcp:
                settings_name = click.prompt("\tSetting name: ", default="")
                ip = click.prompt("\tIP: ", default="")
                subnet_mask = click.prompt("\tSubnet Mask: ", default="")
                gateway_default = click.prompt("\tDefault Gateway: ", default="")
                gateway_alternate = click.prompt("\tAlternate Gateway: ", default="")

                network_settings.append(
                    {
                        "is_dhcp": is_dhcp,
                        "name": settings_name,
                        "ip": ip,
                        "subnet_mask": subnet_mask,
                        "gateway_default": gateway_default,
                        "gateway_alternate": gateway_alternate,
                    }
                )

            else:
                network_settings.append({"is_dhcp": is_dhcp})

            choice = click.prompt(
                "\n{}(y/n)".format(highlight_text("Want to add more networks")),
                default="n",
            )

        click.secho("\nDNS Setting", underline=True)
        dns_primary = click.prompt("\n\tDNS Primary: ", default="")
        dns_secondary = click.prompt("\tDNS Secondary: ", default="")
        dns_tertiary = click.prompt("\tDNS Tertiary: ", default="")
        dns_search_path = click.prompt("\tDNS Search Path: ", default="")

        gc[data].update(
            {
                "network_settings": network_settings,
                "dns_search_path": [dns_search_path],
                "dns_tertiary": dns_tertiary,
                "dns_primary": dns_primary,
                "dns_secondary": dns_secondary,
            }
        )

    return gc


def generate_free_slots(limit):

    slots = []
    for i in range(limit):
        slots.append(i)

    return slots
