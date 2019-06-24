import click
import json

from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.providers import get_provider_interface
from .constants import VCENTER as vmw


Provider = get_provider_interface()


class VCenterVmProvider(Provider):

    provider_type = "VMW_VM"
    package_name = __name__
    spec_template_file = "vmware_vm_provider_spec.yaml.jinja2"

    @classmethod
    def create_spec(cls):
        client = get_api_client()
        create_spec(client)


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
        datastore_name_url_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            url = entity["status"]["resources"]["summary"]["url"]
            datastore_name_url_map[name] = url

        return datastore_name_url_map

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
        storage_pod_list = []
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            storage_pod_list.append(name)

        return storage_pod_list

    def templates(self, account_id):
        Obj = get_resource_api(vmw.TEMPLATE, self.connection)
        payload = {"filter": "account_uuid=={};".format(account_id)}
        res, err = Obj.list(payload)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        template_name_id_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            tem_id = entity["status"]["resources"]["config"]["instanceUuid"]
            template_name_id_map[name] = tem_id

        return template_name_id_map

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
        network_name_id_map = {}
        for entity in res["entities"]:
            name = entity["status"]["resources"]["name"]
            entity_id = entity["status"]["resources"]["id"]

            network_name_id_map[name] = entity_id

        return network_name_id_map

    def file_paths(
        self, account_id, datastore_url=None, file_extension="iso", host_id=None
    ):

        Obj = get_resource_api(vmw.FILE_PATHS, self.connection)
        payload = ""
        if datastore_url:
            payload = {
                "filter": "account_uuid=={};file_extension==iso;datastore_url=={}".format(
                    account_id, file_extension, datastore_url
                )
            }
        else:
            payload = {
                "filter": "account_uuid=={};file_extension==iso;host_id=={}".format(
                    account_id, file_extension, host_id
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

    def template_defaults(self, account_id, template_id):
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
                controllers = entity_config["hardware"]["device"]["controller"]
                disks = entity_config["hardware"]["device"]["disk"]
                networks = entity_config["hardware"]["device"]["network"]
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
                dsk["location"] = disk["backing"]["datastore"]["name"]
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
    click.echo("\nChoose from given projects:")
    for ind, name in enumerate(project_list):
        click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

    if not project_list:
        click.echo(highlight_text("No projects found!!!"))
        click.echo(highlight_text("Please add first"))
        return

    project_id = ""
    while True:
        ind = click.prompt("\nEnter the index of project", default=1)
        if ind > len(project_list):
            click.echo("Invalid index !!! ")

        else:
            project_id = projects[project_list[ind - 1]]
            click.echo("{} selected".format(highlight_text(project_list[ind - 1])))
            break

    res, err = client.project.read(project_id)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    project = res.json()
    accounts = project["status"]["project_status"]["resources"][
        "account_reference_list"
    ]

    res, err = client.account.list()
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    account_id_type_map = {}
    for entity in res["entities"]:
        account_type = entity["status"]["resources"]["type"]
        account_id = entity["metadata"]["uuid"]
        account_id_type_map[account_id] = account_type

    account_id = ""
    for account in accounts:
        if account_id_type_map[account["uuid"]] == "vmware":
            account_id = account["uuid"]
            break

    if not account_id:
        click.echo(highlight_text("No vmware account found woth this project !!!"))
        click.echo("Please add one")
        return

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
                if ind > len(host_names):
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
                if ind > len(datastore_names):
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
                if ind > len(cluster_list):
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
                if ind > len(storage_pod_list):
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
            if ind > len(template_names):
                click.echo("Invalid index !!! ")

            else:
                template_name = template_names[ind - 1]
                template_id = template_name_id_map[template_name]  # TO BE USED
                spec["template"] = template_id
                click.echo("{} selected".format(highlight_text(template_name)))
                break

    spec["name"] = click.prompt("\nEnter instance name", type=str)

    # TODO check for the validation by the spec(as done in AHV)
    spec["resources"] = {}
    spec["resources"]["num_sockets"] = click.prompt("\nEnter no. of vCPUs", default=1)

    spec["resources"]["num_vcpus_per_socket"] = click.prompt(
        "\nCores per vCPU", default=1
    )

    spec["resources"]["memory_size_mib"] = click.prompt("\nMemory(in GB)", default=1)

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
        click.secho("\nConfig of template controllers:", underline=True)
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
                highlight_text("\nWant to edit this controller(y/n)"), default="n"
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
                    if ind > len(controllers):
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
                    if ind > len(sharingOptions):
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
        click.secho("\nSCSI Controllers", bold=True, underline=True)

        for cntlr in tempSATAContrlr:
            click.echo("\n\t\t", nl=False)
            click.secho("SATA CONTROLLER {}\n".format(index + 1), underline=True)

            click.echo(
                "\nController Type: {}".format(highlight_text(cntlr["controller_type"]))
            )
            choice = click.prompt("Want to edit this controller(y/n)", default="n")
            if choice[0] == "y":
                controllers = list(vmw.CONTROLLER["SATA"].keys())
                click.echo("\nChoose from given controller types:")
                for ind, name in enumerate(controllers):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt(
                        "\nEnter the index of controller type", default=1
                    )
                    if ind > len(controllers):
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
        click.secho("\nConfig of template disks:", underline=True)
    else:
        click.echo("\nNo template disks found!!")

    for index, disk in enumerate(tempDisks):
        click.echo("\n\t\t", nl=False)
        click.secho("vDisk {}\n".format(index + 1), underline=True)
        disk_type = disk["disk_type"]
        adapter_type = disk["adapter_type"]

        click.echo("\nDevice Type: {}".format(highlight_text(disk_type)))
        click.echo("Adapter Type: {}".format(highlight_text(adapter_type)))

        if disk_type == "disk":
            click.echo("Size (in GiB): {}".format(highlight_text(disk["size"] // 1024)))
            click.echo("Location : {}".format(highlight_text(disk["location"])))
            controller_label = controller_key_type_map[disk["controller_key"]][1]
            click.echo("Controller: {}".format(highlight_text(controller_label)))
            click.echo("Device Slot: {}".format(highlight_text(disk["device_slot"])))
            click.echo("Disk Mode: {}".format(highlight_text(disk["mode"])))
            click.echo("Exclude from vm config: {}".format(highlight_text("No")))

            choice = click.prompt(
                highlight_text("\nWant to edit this disk(y/n)"), default="n"
            )
            # Only size, disk_mode and excluding checkbox is editable(FROM UI)
            if choice[0] == "y":
                size = click.prompt("\nEnter disk size (in GiB)", default=8)
                click.echo("\nChoose from given disk modes:")

                disk_mode_list = list(vmw.DISK_MODE.keys())
                for ind, name in enumerate(disk_mode_list):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt("\nEnter the index of disk mode", default=1)
                    if ind > len(disk_mode_list):
                        click.echo("Invalid index !!! ")

                    else:
                        disk_mode = disk_mode_list[ind - 1]
                        click.echo("{} selected".format(highlight_text(disk_mode)))
                        disk_mode = vmw.DISK_MODE[disk_mode]
                        break

                is_deleted = click.prompt(
                    "\nExclude disk from vm config(y/n)", default="n"
                )
                is_deleted = True if is_deleted[0] == "y" else False
                dsk = {
                    "disk_size_mb": size * 1024,
                    "is_deleted": is_deleted,
                    "disk_mode": disk_mode,
                    "adapter_type": adapter_type,
                    "disk_type": disk_type,
                    "key": disk["key"],
                }

                spec["resources"]["template_disk_list"].append(dsk)
        else:
            click.echo(highlight_text("\nNo field can be edited in this template disk"))

    if tempNics:
        click.secho("\nConfig of template nics:", underline=True)
    else:
        click.echo("\nNo template nics found!!")

    for index, nic in enumerate(tempNics):
        click.echo("\n\t\t", nl=False)
        click.secho("vNIC-{}\n".format(index + 1), underline=True)
        click.echo("\nAdapter Type: {}".format(highlight_text(nic["nic_type"])))
        click.echo("Network Type: {}".format(highlight_text(nic["net_name"])))
        click.echo("Exclude from vm config: {}".format(highlight_text("No")))

        choice = click.prompt(
            highlight_text("\nWant to edit this nic(y/n)"), default="n"
        )
        if choice[0] == "y":
            click.echo("\nChoose from given network adapters:")
            adapter_types = list(vmw.NetworkAdapterMap.values())
            for ind, name in enumerate(adapter_types):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of adapter type", default=1)
                if ind > len(adapter_types):
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
                if ind > len(network_names):
                    click.echo("Invalid index !!! ")

                else:
                    network_name = network_names[ind - 1]
                    click.echo("{} selected".format(highlight_text(network_name)))
                    network_id = network_name_id_map[network_name]
                    break

            is_deleted = click.prompt(
                "\nExclude network from vm config(y/n)", default="n"
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
    choice = click.prompt("\nWant to add SCSI controllers(y/n)", default="n")
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
            if ind > len(controllers):
                click.echo("Invalid index !!! ")

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
            if ind > len(sharingOptions):
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
            "is_deleted": False,
            "key": key,
        }

        controller_key_type_map[key] = ("SCSI", label)
        spec["resources"]["controller_list"].append(controller)
        choice = click.prompt(
            highlight_text("\nWant to add more SCSI controllers(y/n)"), default="n"
        )

    choice = click.prompt("\nWant to add SATA controllers(y/n)", default="n")
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
            if ind > len(controllers):
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
        controller = {
            "controller_type": controller_type,
            "is_deleted": False,
            "key": key,
        }

        controller_key_type_map[key] = ("SATA", label)
        spec["resources"]["controller_list"].append(controller)
        choice = click.prompt(
            highlight_text("\nWant to add more SATA controllers(y/n)"), default="n"
        )

    choice = click.prompt("\nWant to add disks(y/n)", default="n")
    while choice[0] == "y":
        click.echo("\nChoose from given disk types:")
        disk_types = list(vmw.DISK_TYPES.keys())
        for ind, name in enumerate(disk_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of disk type", default=1)
            if ind > len(disk_types):
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
            if ind > len(disk_adapters):
                click.echo("Invalid index !!! ")

            else:
                adapter_type = disk_adapters[ind - 1]
                click.echo("{} selected".format(highlight_text(adapter_type)))
                adapter_type = vmw.DISK_ADAPTER_TYPES[adapter_type]  # TO BE USED
                break

        if disk_type == "disk":
            disk_size = click.prompt("\nEnter disk size (in GiB)", default=8)

            if not drs_mode:
                datastore_name_url_map = Obj.networks(account_id, host_id=host_id)
            else:
                datastore_name_url_map = Obj.networks(
                    account_id, cluster_name=cluster_name
                )

            locations = list(datastore_name_url_map.keys())
            click.echo("\nChoose from given location:")
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
                    if ind > len(controller):
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
                "device_slot": device_slot,
                "adapter_type": adapter_type,
                "location": datastore_url,
                "controller_key": controller_key,
                "disk_type": disk_type,
            }

        else:
            click.echo(
                highlight_text(
                    "\nBy default, ISO images across all datastores are available for selection. To filter this list, select a datastore.\n"
                )
            )
            datastore_url = None

            choice = click.prompt(
                highlight_text("\nWant to enter datastore(y/n)"), default="y"
            )
            if choice[0] == "y":
                if not drs_mode:
                    datastore_name_url_map = Obj.networks(account_id, host_id=host_id)
                else:
                    datastore_name_url_map = Obj.networks(
                        account_id, cluster_name=cluster_name
                    )

                datastores = list(datastore_name_url_map.keys())
                click.echo("\nChoose from given datastore:")
                for ind, name in enumerate(datastores):
                    click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

                while True:
                    ind = click.prompt("\nEnter the index of datastore", default=1)
                    if ind > len(locations):
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
            else:
                file_paths = Obj.file_paths(account_id, host_id=host_id)

            click.echo("\nChoose from given ISO file paths:")
            for ind, name in enumerate(file_paths):
                click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

            while True:
                ind = click.prompt("\nEnter the index of file path", default=1)
                if ind > len(file_paths):
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
            highlight_text("\nWant to add more disks(y/n)"), default="n"
        )

    click.echo(
        highlight_text(
            "\nNetwork Configuration is needed for Actions and Runbooks to work"
        )
    )
    choice = click.prompt("Want to add nics(y/n)", default="n")
    while choice[0] == "y":
        click.echo("\nChoose from given network adapters:")
        adapter_types = list(vmw.NetworkAdapterMap.values())
        for ind, name in enumerate(adapter_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of adapter type", default=1)
            if ind > len(adapter_types):
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
            highlight_text("\nWant to add more nics(y/n)"), default="n"
        )

    click.secho("\nVM Guest Customization", underline=True)

    gc_enable = click.prompt("Enable Guest Customization(y/n)", default="y")
    if gc_enable:

        click.echo("\nChoose from given Operating System types:")
        os_types = list(vmw.OperatingSystem.keys())
        for ind, name in enumerate(os_types):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt("\nEnter the index of operating system", default=1)
            if ind > len(os_types):
                click.echo("Invalid index !!! ")

            else:
                guest_os = os_types[ind - 1]
                click.echo("{} selected".format(highlight_text(guest_os)))
                guest_os = vmw.OperatingSystem[guest_os]
                break

        click.echo("\nChoose from given Guest Customization Modes:")
        gc_modes = list(vmw.GuestCustomizationModes.keys())
        for ind, name in enumerate(gc_modes):
            click.echo("\t {}. {}".format(str(ind + 1), highlight_text(name)))

        while True:
            ind = click.prompt(
                "\nEnter the index of Guest Customization Mode", default=1
            )
            if ind > len(gc_modes):
                click.echo("Invalid index !!! ")

            else:
                gc_mode = gc_modes[ind - 1]
                click.echo("{} selected".format(highlight_text(gc_mode)))
                gc_mode = vmw.GuestCustomizationModes[gc_mode]
                break


def generate_free_slots(limit):

    slots = []
    for i in range(limit):
        slots.append(i)

    return slots
